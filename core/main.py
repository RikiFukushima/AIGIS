#!/usr/bin/env python3
"""
A.I.G.I.S. エントリーポイント
n8n および CLI から呼び出すインターフェース

使い方:
  python3 main.py "質問内容"
  python3 main.py "質問内容" --session-id <ID> --pretty

出力 (stdout, JSON):
  {
    "output": "最終回答テキスト",
    "agent": "最後に担当したエージェント名",
    "history": ["aigis", "scouter", "aigis"]
  }

ログは stderr に出力されるため、パイプ処理でも JSON が汚染されない。

特殊コマンド:
  python3 main.py --ingest   knowledge/ のドキュメントを ChromaDB に取り込む
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage

# stderr にログを出力（stdout を JSON 専用に保つ）
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

    Returns:
        {
            "output": str,         # 最終回答テキスト
            "agent": str,          # 最後に担当したエージェント
            "history": List[str],  # 関与したエージェントの順序リスト
        }
    """
    graph = get_graph()

    initial_state: AigisState = {
        "messages": [HumanMessage(content=query)],
        "current_task": "",
        "original_query": query,
        "next_agent": "",
        "responding_agent": "",
        "iteration_count": 0,
        "agent_history": [],
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
            "history": [],
        }

    output = _extract_final_output(final_state)
    last_agent = final_state.get("responding_agent", "aigis")
    history = final_state.get("agent_history", [])

    return {
        "output": output,
        "agent": last_agent,
        "history": history,
    }


def _extract_final_output(state: AigisState) -> str:
    """ステートから最終出力テキストを抽出する"""
    # 1. final_answer フィールドが明示的に設定されていれば優先
    if state.get("final_answer"):
        return str(state["final_answer"])

    # 2. 最後の AIMessage から取得
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, AIMessage):
            content = str(msg.content)
            if content.strip():
                return content

    return "回答を生成できませんでした。"


def cmd_ingest() -> None:
    """knowledge/ のドキュメントを ChromaDB に取り込む"""
    from tools.rag import ingest_documents
    print("[AIGIS] ドキュメント取り込みを開始します...", file=sys.stderr)
    count = ingest_documents()
    result = {"status": "success", "chunks_ingested": count}
    print(json.dumps(result, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A.I.G.I.S. - 15エージェント AI システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python3 main.py "今日のドル円レートは？"
  python3 main.py "Pythonでソートアルゴリズムを実装して" --pretty
  python3 main.py --ingest
        """,
    )
    parser.add_argument("query", nargs="?", help="AIGISへの質問・指示")
    parser.add_argument("--session-id", default="default", help="セッションID")
    parser.add_argument("--pretty", action="store_true", help="JSON出力をインデント付きで表示")
    parser.add_argument("--ingest", action="store_true", help="knowledge/のドキュメントをChromaDBに取り込む")

    args = parser.parse_args()

    if args.ingest:
        cmd_ingest()
        return

    if not args.query:
        parser.print_help()
        sys.exit(1)

    result = run(args.query, session_id=args.session_id)

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
