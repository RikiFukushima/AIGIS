"""
A.I.G.I.S. メイングラフ
LangGraph による15エージェントオーケストレーション

グラフ構造:
  START → aigis
  aigis → [14専門家エージェント | END]  (Conditional Edge)
  各専門家 → aigis                       (反復思考ループ)
"""
from __future__ import annotations

import logging
from typing import Union

from langgraph.graph import END, START, StateGraph

from config import MAX_ITERATIONS, ROUTABLE_AGENTS
from state import AigisState
from agents import aigis_node, scouter_node, get_specialist_node

logger = logging.getLogger(__name__)


def _route_from_aigis(state: AigisState) -> Union[str, type]:
    """
    AIGIS の判断を元に次のノードへルーティングする

    Returns:
        ノード名 (str) または END
    """
    next_agent = state.get("next_agent", "FINISH")
    iteration = state.get("iteration_count", 0)

    if next_agent == "FINISH":
        logger.info(f"[Graph] FINISH → END (iteration={iteration})")
        return END

    if iteration >= MAX_ITERATIONS:
        logger.warning(f"[Graph] 反復上限 ({MAX_ITERATIONS}) 到達 → 強制終了")
        return END

    if next_agent not in ROUTABLE_AGENTS:
        logger.error(f"[Graph] 未知エージェント '{next_agent}' → END")
        return END

    logger.info(f"[Graph] aigis → {next_agent} (iter={iteration})")
    return next_agent


def build_graph() -> StateGraph:
    """
    LangGraph の StateGraph を構築して返す

    ノード:
      - aigis: スーパーバイザー
      - scouter: Web検索 (Priority 1 実装)
      - deus, archive, matrix, vibe: ツール付き実装
      - chronos, valor, palette, zenon, signal, justice, vita, babel, mumon: 汎用実装
    """
    builder = StateGraph(AigisState)

    # ===== ノード追加 =====

    # スーパーバイザー
    builder.add_node("aigis", aigis_node)

    # Scouter (直接インポート)
    builder.add_node("scouter", scouter_node)

    # 残り13名のスペシャリスト
    for agent_name in ROUTABLE_AGENTS:
        if agent_name == "scouter":
            continue
        node_fn = get_specialist_node(agent_name)
        builder.add_node(agent_name, node_fn)
        logger.debug(f"ノード追加: {agent_name}")

    # ===== エッジ定義 =====

    # エントリーポイント: START → aigis
    builder.add_edge(START, "aigis")

    # aigis → 条件分岐（14専門家 または END）
    routing_map = {name: name for name in ROUTABLE_AGENTS}
    routing_map[END] = END
    builder.add_conditional_edges("aigis", _route_from_aigis, routing_map)

    # 全専門家 → aigis へ戻る（反復思考ループ）
    for agent_name in ROUTABLE_AGENTS:
        builder.add_edge(agent_name, "aigis")

    return builder.compile()


# ===== シングルトン =====
_graph_instance = None


def get_graph():
    global _graph_instance
    if _graph_instance is None:
        logger.info("[Graph] グラフをビルド中...")
        _graph_instance = build_graph()
        logger.info("[Graph] ビルド完了")
    return _graph_instance
