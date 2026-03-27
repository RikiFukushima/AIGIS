"""
Scouter（探査官） - Web検索エージェント
DuckDuckGo を使ってリアルタイム情報を収集する
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from state import AigisState
from tools.search import get_search_tools
from .base import build_llm, load_prompt

logger = logging.getLogger(__name__)

_scouter_llm = build_llm(temperature=0.2)
_search_tools = get_search_tools()


def scouter_node(state: AigisState) -> Dict[str, Any]:
    """Scouter ノード: DuckDuckGo 検索で情報収集"""
    system_prompt = load_prompt("scouter")

    agent = create_react_agent(
        model=_scouter_llm,
        tools=_search_tools,
        state_modifier=system_prompt,
    )

    result = agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    search_result = ""
    for msg in reversed(new_messages):
        if isinstance(msg, AIMessage):
            search_result = str(msg.content)
            break

    logger.info(f"[Scouter] 検索完了 ({len(new_messages)} メッセージ)")

    return {
        "messages": new_messages,
        "responding_agent": "scouter",
        "agent_history": ["scouter"],
        "collected_data": {"scouter_result": search_result},
    }
