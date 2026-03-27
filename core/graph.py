"""
A.I.G.I.S. メイングラフ
LangGraph による15エージェントのオーケストレーション
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
    アイギスの判断を元に次のノードへルーティングする
    - FINISH または反復上限超過 → END
    - それ以外 → 対応するエージェントノード名
    """
    next_agent = state.get("next_agent", "FINISH")
    iteration = state.get("iteration_count", 0)

    if next_agent == "FINISH":
        logger.info(f"[Graph] FINISH → END (iteration={iteration})")
        return END

    if iteration >= MAX_ITERATIONS:
        logger.warning(f"[Graph] 反復上限 ({MAX_ITERATIONS}) に達しました → END")
        return END

    if next_agent not in ROUTABLE_AGENTS:
        logger.error(f"[Graph] 不明なエージェント: {next_agent} → END")
        return END

    logger.info(f"[Graph] → {next_agent} (iteration={iteration})")
    return next_agent


def build_graph() -> StateGraph:
    """
    グラフを構築して返す

    構造:
        START → aigis
        aigis → [scouter | deus | ... 各スペシャリスト | END] (条件分岐)
        各スペシャリスト → aigis  (結果をスーパーバイザーへ返す)
    """
    builder = StateGraph(AigisState)

    # ===== ノード追加 =====

    # スーパーバイザー
    builder.add_node("aigis", aigis_node)

    # Priority 1: 実装済みエージェント
    builder.add_node("scouter", scouter_node)

    # Priority 2: スペシャリスト（汎用ノード or 個別実装）
    for agent_name in ROUTABLE_AGENTS:
        if agent_name == "scouter":
            continue  # 既に追加済み
        node_fn = get_specialist_node(agent_name)
        builder.add_node(agent_name, node_fn)

    # ===== エッジ定義 =====

    # エントリーポイント
    builder.add_edge(START, "aigis")

    # アイギス → 条件分岐
    routing_map = {name: name for name in ROUTABLE_AGENTS}
    routing_map[END] = END
    builder.add_conditional_edges("aigis", _route_from_aigis, routing_map)

    # 全スペシャリスト → アイギスへ戻る（反復思考ループ）
    for agent_name in ROUTABLE_AGENTS:
        builder.add_edge(agent_name, "aigis")

    return builder.compile()


# シングルトンインスタンス（起動時に1度だけビルド）
_graph_instance = None


def get_graph():
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
    return _graph_instance
