"""
アイギス - スーパーバイザー / ルーター
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

# ルーティング判断用の軽量LLM（temperature低め）
_router_llm = build_llm(temperature=0.2)


def _build_routing_prompt(state: AigisState) -> str:
    """ルーティング判断用のプロンプトを構築する"""
    agent_list = "\n".join(
        f"- {name}: {AGENT_REGISTRY[name].description}"
        for name in ROUTABLE_AGENTS
    )
    last_response = extract_last_ai_content(state["messages"]) or "なし"

    return f"""あなたはA.I.G.I.S.の中枢、統括執事アイギスです。

## 利用可能な専門エージェント
{agent_list}
- FINISH: タスクが完了した場合（最終回答の準備ができた場合）

## 現在の状況
- ユーザーの元の質問: {state.get('original_query', '不明')}
- 現在のタスク: {state.get('current_task', '不明')}
- 繰り返し回数: {state.get('iteration_count', 0)}
- 直前のエージェントの回答: {last_response[:500] if last_response else 'なし'}

## 指示
上記の状況を分析し、次に呼び出すべきエージェントを1つ選んでください。
タスクが完了した場合は FINISH を選んでください。

必ず以下のJSON形式のみで回答してください（他のテキストは不要）:
{{
  "next_agent": "<エージェント名またはFINISH>",
  "reasoning": "<30字以内で判断理由>"
}}"""


def aigis_node(state: AigisState) -> Dict[str, Any]:
    """
    アイギス スーパーバイザーノード
    - 初回: タスクを理解し最初の専門家を選ぶ
    - 2回目以降: 前の専門家の結果を見て次のアクションを決める
    """
    system_prompt = load_prompt("aigis")
    routing_prompt = _build_routing_prompt(state)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=routing_prompt),
    ]

    try:
        response = _router_llm.invoke(messages)
        content = str(response.content).strip()

        # JSON 抽出（コードブロックで囲まれている場合も対応）
        json_match = re.search(r'\{[^{}]+\}', content, re.DOTALL)
        if json_match:
            decision = json.loads(json_match.group())
            next_agent = decision.get("next_agent", "FINISH").strip()
            reasoning = decision.get("reasoning", "")
        else:
            # フォールバック: テキストからエージェント名を探す
            next_agent = _parse_agent_from_text(content)
            reasoning = "テキストパース"

        # バリデーション
        valid_targets = set(ROUTABLE_AGENTS) | {"FINISH"}
        if next_agent not in valid_targets:
            logger.warning(f"不明なエージェント '{next_agent}' → FINISH にフォールバック")
            next_agent = "FINISH"

        logger.info(f"[Aigis] → {next_agent} (理由: {reasoning})")

    except Exception as e:
        logger.error(f"[Aigis] ルーティングエラー: {e}")
        next_agent = "FINISH"

    # 初回の場合は current_task を設定
    updates: Dict[str, Any] = {
        "next_agent": next_agent,
        "responding_agent": "aigis",
        "iteration_count": state.get("iteration_count", 0) + 1,
    }

    if not state.get("current_task") and state.get("messages"):
        last_human = next(
            (m.content for m in reversed(state["messages"])
             if isinstance(m, HumanMessage)), ""
        )
        updates["current_task"] = str(last_human)[:200]

    return updates


def _parse_agent_from_text(text: str) -> str:
    """JSONパース失敗時のフォールバック: テキストからエージェント名を抽出"""
    text_lower = text.lower()
    for name in ROUTABLE_AGENTS:
        if name in text_lower:
            return name
    if "finish" in text_lower or "完了" in text:
        return "FINISH"
    return "FINISH"
