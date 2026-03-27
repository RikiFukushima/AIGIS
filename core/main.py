#!/usr/bin/env python3
"""
A.I.G.I.S. エントリーポイント
n8n から呼び出すCLIインターフェース

使い方:
    python3 main.py "質問内容"
    python3 main.py "質問内容" --session-id <セッションID>

出力 (stdout, JSON):
    {"output": "回答内容", "agent": "最後に担当したエージェント名"}
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict

from langchain_core.messages import HumanMessage

# ロギング設定（stderr に出力してstdoutをJSONに保つ）
log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.WARNING),
    stream=sys.stderr,
    format="[%(levelname)s] %(name)s: %(message)s",
)

from graph import get_graph
from state import AigisState


def run(query: str, session_id: str = "default") -> Dict[str, Any]:
    """
    グラフを実行して最終回答を返す

    Args:
        query: ユーザーの質問文
        session_id: セッション識別子（将来の会話履歴管理用）

    Returns:
        {"output": str, "agent": str}
    """
    graph = get_graph()

    initial_state: AigisState = {
        "messages": [HumanMessage(content=query)],
        "current_task": "",
        "original_query": query,
        "next_agent": "",
        "responding_agent": "",
        "iteration_count": 0,
        "collected_data": {},
        "final_answer": None,
    }

    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        logging.error(f"グラフ実行エラー: {e}", exc_info=True)
        return {
            "output": f"処理中にエラーが発生しました: {str(e)}",
            "agent": "system",
        }

    # 最終回答の抽出
    output = _extract_final_output(final_state)
    last_agent = final_state.get("responding_agent", "aigis")

    return {
        "output": output,
        "agent": last_agent,
    }


def _extract_final_output(state: AigisState) -> str:
    """ステートから最終的な出力テキストを抽出する"""
    # 1. final_answer フィールドが設定されていれば優先
    if state.get("final_answer"):
        return state["final_answer"]

    # 2. 最後のAIメッセージから取得
    from langchain_core.messages import AIMessage
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, AIMessage):
            content = str(msg.content)
            if content.strip():
                return content

    # 3. フォールバック
    return "回答を生成できませんでした。"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A.I.G.I.S. - 15エージェントAIシステム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python3 main.py "今日の東京の天気は？"
  python3 main.py "Pythonでフィボナッチ数列を実装して" --session-id user123
        """,
    )
    parser.add_argument("query", help="AIGISへの質問・指示")
    parser.add_argument(
        "--session-id",
        default="default",
        help="セッションID（デフォルト: default）",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="JSON出力をインデント付きで表示（デバッグ用）",
    )

    args = parser.parse_args()

    result = run(args.query, session_id=args.session_id)

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
