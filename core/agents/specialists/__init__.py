"""
残り13名の専門エージェント
各エージェントはプロンプトを読み込む汎用実装。
ツールが必要なエージェント（deus等）は個別モジュールで拡張する。
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from config import AGENT_REGISTRY
from state import AigisState
from agents.base import build_llm, load_prompt

logger = logging.getLogger(__name__)

# デウスのみShellToolを個別インポート（存在する場合）
try:
    from .deus import deus_node as _deus_node
    _HAS_DEUS = True
except ImportError:
    _HAS_DEUS = False


def _make_generic_node(agent_name: str) -> Callable[[AigisState], Dict[str, Any]]:
    """
    汎用エージェントノードファクトリ
    プロンプトを読み込み、LLMで回答を生成する
    """
    llm = build_llm(temperature=0.7)

    def node(state: AigisState) -> Dict[str, Any]:
        system_prompt = load_prompt(agent_name)
        display_name = AGENT_REGISTRY[agent_name].display_name

        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        result_content = str(response.content)

        logger.info(f"[{display_name}] 回答生成完了")

        return {
            "messages": [AIMessage(content=result_content, name=agent_name)],
            "responding_agent": agent_name,
            "collected_data": {f"{agent_name}_result": result_content},
        }

    node.__name__ = f"{agent_name}_node"
    return node


# 各スペシャリストノードを生成
_SPECIALIST_NAMES = [
    "deus", "kronos", "archive", "logos", "hephaestus",
    "hermes", "athena", "muse", "argos", "sophia",
    "gaia", "nemesis", "prometheus",
]

_nodes: Dict[str, Callable] = {}
for _name in _SPECIALIST_NAMES:
    if _name == "deus" and _HAS_DEUS:
        _nodes["deus"] = _deus_node
    else:
        _nodes[_name] = _make_generic_node(_name)


def get_specialist_node(agent_name: str) -> Callable[[AigisState], Dict[str, Any]]:
    """エージェント名に対応するノード関数を返す"""
    if agent_name not in _nodes:
        raise KeyError(f"未知のスペシャリスト: {agent_name}")
    return _nodes[agent_name]


__all__ = ["get_specialist_node"]
