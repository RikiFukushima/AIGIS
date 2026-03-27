"""
スカウター - Web検索エージェント
DuckDuckGo を使ってリアルタイム情報を収集する
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from state import AigisState
from tools.search import get_search_tools
from .base import build_llm, load_prompt

logger = logging.getLogger(__name__)

_scouter_llm = build_llm(temperature=0.3)
_search_tools = get_search_tools()


def scouter_node(state: AigisState) -> Dict[str, Any]:
    """
    スカウター ノード
    DuckDuckGo でWeb検索を行い、収集データと回答をステートに追加する
    """
    system_prompt = load_prompt("scouter")

    # create_react_agent で検索ツール付きエージェントを構築
    agent = create_react_agent(
        model=_scouter_llm,
        tools=_search_tools,
        state_modifier=system_prompt,
    )

    # 現在のメッセージをエージェントに渡す
    result = agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    # 最後のAIメッセージを検索結果として保存
    search_result = ""
    for msg in reversed(new_messages):
        if isinstance(msg, AIMessage):
            search_result = str(msg.content)
            break

    logger.info(f"[Scouter] 検索完了 ({len(new_messages)} メッセージ追加)")

    return {
        "messages": new_messages,
        "responding_agent": "scouter",
        "collected_data": {"scouter_result": search_result},
    }
