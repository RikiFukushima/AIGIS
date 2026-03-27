"""
A.I.G.I.S. 共有ステート定義
全エージェントが参照・更新する中央状態
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage


def _merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """辞書をマージする（後勝ち）"""
    return {**a, **b}


class AigisState(TypedDict):
    # --- 会話履歴 (追記式) ---
    messages: Annotated[List[BaseMessage], operator.add]

    # --- タスク情報 ---
    current_task: str           # 現在処理中のタスク概要
    original_query: str         # ユーザーの元の質問

    # --- エージェント制御 ---
    next_agent: str             # 次に呼び出すエージェント名 ("FINISH" で終了)
    responding_agent: str       # 最後に回答したエージェント名
    iteration_count: int        # ループ回数（無限ループ防止）

    # --- データ収集 (マージ式) ---
    collected_data: Annotated[Dict[str, Any], _merge_dicts]

    # --- 最終出力 ---
    final_answer: Optional[str]
