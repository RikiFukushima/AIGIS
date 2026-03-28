"""
Vibe（予言者） - SNSトレンド・感情分析エージェント
DuckDuckGo 検索でトレンドを収集し、感情分析を行う
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from state import AigisState
from tools.search import get_search_tools
from agents.base import build_llm, load_prompt

logger = logging.getLogger(__name__)

_vibe_llm = build_llm(temperature=0.5)


def vibe_node(state: AigisState) -> Dict[str, Any]:
    """Vibe ノード: Web検索でトレンドを収集して感情・バズ分析を行う"""
    system_prompt = load_prompt("vibe")
    search_tools = get_search_tools()

    if not search_tools:
        # 検索ツールなし → テキスト分析のみ
        from langchain_core.messages import SystemMessage
        from agents.base import build_llm
        llm = build_llm(temperature=0.5)
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        result = str(response.content)
        return {
            "messages": [AIMessage(content=result, name="vibe")],
            "responding_agent": "vibe",
            "agent_history": ["vibe"],
            "collected_data": {"vibe_result": result},
        }

    agent = create_react_agent(
        model=_vibe_llm,
        tools=search_tools,
        state_modifier=system_prompt,
    )

    result = agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    trend_result = ""
    for msg in reversed(new_messages):
        if isinstance(msg, AIMessage):
            trend_result = str(msg.content)
            break

    logger.info(f"[Vibe] トレンド分析完了")

    return {
        "messages": new_messages,
        "responding_agent": "vibe",
        "agent_history": ["vibe"],
        "collected_data": {"vibe_result": trend_result},
    }
