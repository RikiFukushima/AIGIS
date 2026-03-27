"""
デウス - シェルコマンド実行エージェント
Mac のターミナルコマンドを安全に実行する
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from state import AigisState
from tools.shell import get_shell_tools
from agents.base import build_llm, load_prompt

logger = logging.getLogger(__name__)

_deus_llm = build_llm(temperature=0.1)  # コマンド実行は低温度で確実に


def deus_node(state: AigisState) -> Dict[str, Any]:
    """
    デウス ノード
    ShellTool を使ってシステムコマンドを実行する
    """
    system_prompt = load_prompt("deus")
    shell_tools = get_shell_tools()

    agent = create_react_agent(
        model=_deus_llm,
        tools=shell_tools,
        state_modifier=system_prompt,
    )

    result = agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    exec_result = ""
    for msg in reversed(new_messages):
        if isinstance(msg, AIMessage):
            exec_result = str(msg.content)
            break

    logger.info(f"[Deus] コマンド実行完了")

    return {
        "messages": new_messages,
        "responding_agent": "deus",
        "collected_data": {"deus_result": exec_result},
    }
