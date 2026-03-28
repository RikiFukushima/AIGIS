"""
A.I.G.I.S. 共有ステート定義
全15エージェントが参照・更新する中央状態
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage


def _merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}


class AigisState(TypedDict):
    # 会話履歴 (追記式)
    messages: Annotated[List[BaseMessage], operator.add]

    # タスク情報
    current_task: str
    original_query: str

    # エージェント制御
    next_agent: str
    responding_agent: str
    iteration_count: int

    # エージェント関与履歴 (追記式) ← NEW
    agent_history: Annotated[List[str], operator.add]

    # データ収集 (マージ式)
    collected_data: Annotated[Dict[str, Any], _merge_dicts]

    # 最終出力
    final_answer: Optional[str]
