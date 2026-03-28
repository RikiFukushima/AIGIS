"""
Deus（工機官） - システム実行エージェント
ShellTool で Mac のコマンド・スクリプトを実行する
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from state import AigisState
from tools.shell import get_shell_tools
from agents.base import build_llm, load_prompt

logger = logging.getLogger(__name__)

# コマンド実行は低温度で確実・安全に
_deus_llm = build_llm(temperature=0.1)


def deus_node(state: AigisState) -> Dict[str, Any]:
    """Deus ノード: ShellTool でシステムコマンドを実行する"""
    system_prompt = load_prompt("deus")
    shell_tools = get_shell_tools()

    if not shell_tools:
        logger.warning("[Deus] ShellTool なし → テキスト回答モード")
        from langchain_core.messages import SystemMessage
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = _deus_llm.invoke(messages)
        result = str(response.content)
        return {
            "messages": [AIMessage(content=result, name="deus")],
            "responding_agent": "deus",
            "agent_history": ["deus"],
            "collected_data": {"deus_result": result},
        }

    agent = create_react_agent(
        model=_deus_llm,
        tools=shell_tools,
        prompt=system_prompt,
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
        "agent_history": ["deus"],
        "collected_data": {"deus_result": exec_result},
    }
