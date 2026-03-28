"""
Matrix（解析官） - データ分析エージェント
PythonREPL を使って統計解析・数値計算を実行する
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from state import AigisState
from tools.python_repl import get_python_repl_tools
from agents.base import build_llm, load_prompt

logger = logging.getLogger(__name__)

# 分析は低温度で正確に
_matrix_llm = build_llm(temperature=0.1)


def matrix_node(state: AigisState) -> Dict[str, Any]:
    """Matrix ノード: PythonREPL で統計計算・データ分析を実行"""
    system_prompt = load_prompt("matrix")
    repl_tools = get_python_repl_tools()

    if not repl_tools:
        logger.warning("[Matrix] PythonREPLTool なし → テキスト回答モード")
        from langchain_core.messages import SystemMessage
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = _matrix_llm.invoke(messages)
        msg = AIMessage(content=str(response.content), name="matrix")
        return {
            "messages": [msg],
            "responding_agent": "matrix",
            "agent_history": ["matrix"],
            "collected_data": {"matrix_result": str(response.content)},
        }

    agent = create_react_agent(
        model=_matrix_llm,
        tools=repl_tools,
        prompt=system_prompt,
    )

    result = agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    analysis_result = ""
    for msg in reversed(new_messages):
        if isinstance(msg, AIMessage):
            analysis_result = str(msg.content)
            break

    logger.info(f"[Matrix] 分析完了")

    return {
        "messages": new_messages,
        "responding_agent": "matrix",
        "agent_history": ["matrix"],
        "collected_data": {"matrix_result": analysis_result},
    }
