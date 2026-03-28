"""
AIGIS - スーパーバイザー / ルーター
全タスクの入口として機能し、最適な専門エージェントへ振り分ける
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from config import AGENT_REGISTRY, ROUTABLE_AGENTS
from state import AigisState
from .base import build_llm, extract_last_ai_content, load_prompt

logger = logging.getLogger(__name__)

# ルーティング用 LLM（低温度で確実な JSON 出力）
_router_llm = build_llm(temperature=0.1)
# 最終回答統合用 LLM
_synthesis_llm = build_llm(temperature=0.3)


_KEYWORD_HINTS: dict[str, list[str]] = {
    "scouter": ["検索", "調べて", "最新", "ニュース", "今日の", "天気", "リアルタイム"],
    "chronos": ["計画", "戦略", "プラン", "ロードマップ", "段階的", "ステップ", "進め方"],
    "deus": ["コード", "スクリプト", "プログラム", "バグ", "実装", "API", "シェル", "自動化", "デプロイ"],
    "archive": ["前に話した", "過去の", "保存", "ナレッジ", "記録", "履歴"],
    "valor": ["投資", "株", "為替", "ポートフォリオ", "財務", "家計", "節税", "経済", "FX"],
    "palette": ["デザイン", "画像", "ロゴ", "UI", "配色", "イラスト", "ビジュアル"],
    "zenon": ["セキュリティ", "安全", "脆弱性", "パスワード", "VPN", "プライバシー", "漏洩"],
    "signal": ["メール", "手紙", "提案書", "挨拶文", "代筆", "文書", "スピーチ", "交渉"],
    "matrix": ["分析", "統計", "CSV", "グラフ", "回帰", "相関", "データ", "計算"],
    "justice": ["契約", "法律", "規約", "著作権", "コンプライアンス", "法的", "労働法"],
    "vibe": ["トレンド", "SNS", "Twitter", "バズ", "評判", "世論", "炎上"],
    "vita": ["健康", "運動", "睡眠", "筋トレ", "食事", "集中力", "生産性", "ダイエット"],
    "babel": ["翻訳", "英訳", "和訳", "多言語", "ローカライズ", "英語で", "フランス語", "中国語"],
    "mumon": ["悩み", "ストレス", "モヤモヤ", "哲学", "瞑想", "内省", "人生", "メンタル"],
}


def _detect_keyword_hints(query: str) -> str:
    """質問文のキーワードからエージェント候補を提示する"""
    if not query:
        return ""
    matches = []
    for agent, keywords in _KEYWORD_HINTS.items():
        hit = [kw for kw in keywords if kw in query]
        if hit:
            matches.append(f"  - {agent}（キーワード: {', '.join(hit)}）")
    if matches:
        return "## キーワード分析による候補\n" + "\n".join(matches) + "\n※ これはヒントです。最終判断は質問の意図を総合的に分析して行ってください。\n"
    return ""


def _build_routing_context(state: AigisState) -> str:
    """ルーティング判断プロンプトを生成する"""
    # エージェント一覧（説明付き）
    agent_list = "\n".join(
        f"- {name}: {AGENT_REGISTRY[name].description}"
        for name in ROUTABLE_AGENTS
    )

    last_response = extract_last_ai_content(state.get("messages", [])) or "なし"
    history = state.get("agent_history", [])
    history_str = " → ".join(history) if history else "なし（初回）"
    original_query = state.get("original_query", "不明")

    # キーワードヒントを生成
    keyword_hint = _detect_keyword_hints(original_query) if not history or history == ["aigis"] else ""

    # 直近で同じエージェントが連続して呼ばれていないかチェック
    repeat_warning = ""
    if len(history) >= 2:
        # aigis を除いた専門家の履歴
        specialists = [h for h in history if h != "aigis"]
        if len(specialists) >= 2 and specialists[-1] == specialists[-2]:
            repeat_warning = f"\n⚠️ 注意: {specialists[-1]} が連続呼び出しされています。同じ専門家を再び選ばず、FINISH または別の専門家を選んでください。"

    return f"""## 判断材料
ユーザーの元の質問: {original_query}
現在のタスク: {state.get('current_task', '未設定')}
これまでの専門家呼び出し履歴: {history_str}
直前の専門家の回答（先頭500字）: {str(last_response)[:500]}
繰り返し回数: {state.get('iteration_count', 0)}{repeat_warning}

{keyword_hint}## 利用可能な専門家
{agent_list}
- FINISH: 十分な回答が得られた / タスクが完了した場合

## ルーティング判断ルール
1. 挨拶・雑談・一般知識で答えられる質問 → **FINISH**（専門家不要）
2. リアルタイムの外部情報が必要 → **scouter**
3. 翻訳が主目的 → **babel**（signalではない）
4. コード・プログラミング → **deus**
5. 文書・メール作成 → **signal**
6. データ分析・数値計算 → **matrix**
7. 前回の専門家が十分な回答を返している → **FINISH**
8. Scouterは「最新情報」「外部検索」が明確に必要な場合のみ選ぶこと

必ず以下のJSON形式のみで回答（他のテキスト・説明は不要）:
{{
  "next_agent": "<エージェント名またはFINISH>",
  "reasoning": "<判断理由を20字以内>"
}}"""


def aigis_node(state: AigisState) -> Dict[str, Any]:
    """
    AIGIS スーパーバイザーノード

    - 初回: 質問を解析して最初の専門家を選択
    - 2回目以降: 前回の結果を見て継続/完了を判断
    """
    system_prompt = load_prompt("aigis")
    routing_context = _build_routing_context(state)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=routing_context),
    ]

    try:
        response = _router_llm.invoke(messages)
        content = str(response.content).strip()

        # JSON 抽出（コードブロック対応）
        json_match = re.search(r'\{[^{}]+\}', content, re.DOTALL)
        if json_match:
            decision = json.loads(json_match.group())
            next_agent = str(decision.get("next_agent", "FINISH")).strip()
            reasoning = decision.get("reasoning", "")
        else:
            next_agent = _fallback_parse(content)
            reasoning = "フォールバックパース"

        # バリデーション
        valid = set(ROUTABLE_AGENTS) | {"FINISH"}
        if next_agent not in valid:
            logger.warning(f"[AIGIS] 不明なエージェント '{next_agent}' → FINISH")
            next_agent = "FINISH"

        logger.info(f"[AIGIS] → {next_agent} ({reasoning})")

    except Exception as e:
        logger.error(f"[AIGIS] ルーティングエラー: {e}")
        next_agent = "FINISH"

    updates: Dict[str, Any] = {
        "next_agent": next_agent,
        "responding_agent": "aigis",
        "iteration_count": state.get("iteration_count", 0) + 1,
        "agent_history": ["aigis"],
    }

    # 初回のみ current_task を設定
    if not state.get("current_task") and state.get("messages"):
        last_human = next(
            (str(m.content) for m in reversed(state["messages"])
             if isinstance(m, HumanMessage)), ""
        )
        updates["current_task"] = last_human[:200]

    # FINISH 時に収集データを統合した最終回答を生成
    if next_agent == "FINISH":
        final = _generate_final_answer(state)
        if final:
            updates["messages"] = [AIMessage(content=final, name="aigis")]
            updates["final_answer"] = final

    return updates


def _generate_final_answer(state: AigisState) -> str:
    """収集データを統合して最終回答を生成する"""
    collected = state.get("collected_data", {})
    original_query = state.get("original_query", "")

    if not collected:
        return ""

    # 収集データのサマリーを作成
    data_summary = "\n".join(
        f"【{key}】\n{str(value)[:800]}"
        for key, value in collected.items()
    )

    synthesis_prompt = f"""あなたはAIGIS、主人に仕える全知の執事です。
以下の専門家たちの回答を統合し、主人の質問に対する最終的な回答を作成してください。

## 主人の質問
{original_query}

## 専門家たちの回答
{data_summary}

## 指示
- 専門家の回答を統合し、簡潔で分かりやすい最終回答を作成すること
- 冗長な繰り返しを避け、要点をまとめること
- 執事らしい丁寧な口調で回答すること
- JSON形式ではなく、自然な文章で回答すること"""

    try:
        response = _synthesis_llm.invoke([
            SystemMessage(content=load_prompt("aigis")),
            HumanMessage(content=synthesis_prompt),
        ])
        return str(response.content).strip()
    except Exception as e:
        logger.error(f"[AIGIS] 最終回答生成エラー: {e}")
        # フォールバック: 最後の収集データをそのまま返す
        last_value = list(collected.values())[-1] if collected else ""
        return str(last_value)


def _fallback_parse(text: str) -> str:
    """JSON パース失敗時にテキストからエージェント名を抽出"""
    text_lower = text.lower()
    for name in ROUTABLE_AGENTS:
        if name in text_lower:
            return name
    return "FINISH"
