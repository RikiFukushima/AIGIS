"""
精鋭14名のスペシャリストエージェント

ツール付き実装:
  - archive.py  (ChromaDB RAG)
  - matrix.py   (PythonREPL)
  - vibe.py     (DuckDuckGo + 感情分析)
  - deus.py     (ShellTool)

汎用実装 (プロンプト読み込み):
  chronos, valor, palette, zenon, signal, justice, vita, babel, mumon
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from langchain_core.messages import AIMessage, SystemMessage

from config import AGENT_REGISTRY
from state import AigisState
from agents.base import build_llm, load_prompt

logger = logging.getLogger(__name__)

# ツール付きエージェントの個別インポート（失敗してもシステムは起動）
_tool_nodes: Dict[str, Callable] = {}

try:
    from .archive import archive_node
    _tool_nodes["archive"] = archive_node
except Exception as e:
    logger.warning(f"archive モジュール読み込みスキップ: {e}")

try:
    from .matrix import matrix_node
    _tool_nodes["matrix"] = matrix_node
except Exception as e:
    logger.warning(f"matrix モジュール読み込みスキップ: {e}")

try:
    from .vibe import vibe_node
    _tool_nodes["vibe"] = vibe_node
except Exception as e:
    logger.warning(f"vibe モジュール読み込みスキップ: {e}")

try:
    from .deus import deus_node
    _tool_nodes["deus"] = deus_node
except Exception as e:
    logger.warning(f"deus モジュール読み込みスキップ: {e}")


def _make_generic_node(agent_name: str) -> Callable[[AigisState], Dict[str, Any]]:
    """汎用エージェントノードファクトリ（ツールなし、プロンプトのみ）"""
    llm = build_llm(temperature=0.7)
    display_name = AGENT_REGISTRY[agent_name].display_name

    def node(state: AigisState) -> Dict[str, Any]:
        system_prompt = load_prompt(agent_name)
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        result_content = str(response.content)

        logger.info(f"[{display_name}] 回答生成完了")

        return {
            "messages": [AIMessage(content=result_content, name=agent_name)],
            "responding_agent": agent_name,
            "agent_history": [agent_name],
            "collected_data": {f"{agent_name}_result": result_content},
        }

    node.__name__ = f"{agent_name}_node"
    return node


# 汎用ノードが必要なエージェント（ツール不要な9名）
_GENERIC_NAMES = [
    "chronos", "valor", "palette", "zenon", "signal",
    "justice", "vita", "babel", "mumon",
]

_all_nodes: Dict[str, Callable] = {}

# ツール付きノードを先に登録
_all_nodes.update(_tool_nodes)

# 汎用ノードを登録（ツール付きが既にある場合はスキップ）
for _name in _GENERIC_NAMES:
    if _name not in _all_nodes:
        _all_nodes[_name] = _make_generic_node(_name)


def get_specialist_node(agent_name: str) -> Callable[[AigisState], Dict[str, Any]]:
    """エージェント名に対応するノード関数を返す"""
    if agent_name not in _all_nodes:
        # フォールバック: 汎用ノードを動的生成
        logger.warning(f"未登録のスペシャリスト '{agent_name}' → 汎用ノードで対応")
        _all_nodes[agent_name] = _make_generic_node(agent_name)
    return _all_nodes[agent_name]


__all__ = ["get_specialist_node"]
