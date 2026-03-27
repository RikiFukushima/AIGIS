"""
AIGIS - スーパーバイザー / ルーター
全タスクの入口として機能し、最適な専門エージェントへ振り分ける
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from config import AGENT_REGISTRY, ROUTABLE_AGENTS
from state import AigisState
from .base import build_llm, extract_last_ai_content, load_prompt

logger = logging.getLogger(__name__)

# ルーティング用 LLM（低温度で確実な JSON 出力）
_router_llm = build_llm(temperature=0.1)


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

    return f"""## 判断材料
ユーザーの元の質問: {state.get('original_query', '不明')}
現在のタスク: {state.get('current_task', '未設定')}
これまでの専門家呼び出し履歴: {history_str}
直前の専門家の回答（先頭500字）: {str(last_response)[:500]}
繰り返し回数: {state.get('iteration_count', 0)}

## 利用可能な専門家
{agent_list}
- FINISH: 十分な回答が得られた / タスクが完了した場合

## 指示
上記を分析し、次のアクションを決定してください。
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

    return updates


def _fallback_parse(text: str) -> str:
    """JSON パース失敗時にテキストからエージェント名を抽出"""
    text_lower = text.lower()
    for name in ROUTABLE_AGENTS:
        if name in text_lower:
            return name
    return "FINISH"
