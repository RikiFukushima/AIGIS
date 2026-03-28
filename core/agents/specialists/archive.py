"""
Archive（記録官） - RAG エージェント
ChromaDB を使ったローカル知識ベース検索
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from state import AigisState
from tools.rag import get_rag_tools
from agents.base import build_llm, load_prompt

logger = logging.getLogger(__name__)

_archive_llm = build_llm(temperature=0.3)


def archive_node(state: AigisState) -> Dict[str, Any]:
    """Archive ノード: ChromaDB でローカル知識ベースを検索"""
    system_prompt = load_prompt("archive")
    rag_tools = get_rag_tools()

    if not rag_tools:
        # ChromaDB が未準備の場合、その旨を回答
        logger.info("[Archive] RAGツールなし → 直接回答モード")
        from langchain_core.messages import AIMessage as AI
        msg = AI(
            content=(
                "【Archive】知識ベースがまだ構築されていません。\n"
                "~/Aigis/knowledge/ にドキュメントを配置後、以下を実行してください:\n"
                "  python3 -c \"from tools.rag import ingest_documents; ingest_documents()\""
            ),
            name="archive",
        )
        return {
            "messages": [msg],
            "responding_agent": "archive",
            "agent_history": ["archive"],
            "collected_data": {"archive_result": "知識ベース未構築"},
        }

    agent = create_react_agent(
        model=_archive_llm,
        tools=rag_tools,
        state_modifier=system_prompt,
    )

    result = agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]

    retrieved = ""
    for msg in reversed(new_messages):
        if isinstance(msg, AIMessage):
            retrieved = str(msg.content)
            break

    logger.info(f"[Archive] 検索完了")

    return {
        "messages": new_messages,
        "responding_agent": "archive",
        "agent_history": ["archive"],
        "collected_data": {"archive_result": retrieved},
    }
