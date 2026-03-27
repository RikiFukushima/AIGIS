"""
Python REPL ツール - Matrix 用
統計計算・データ分析コードをリアルタイムで実行する
"""
from __future__ import annotations

import logging
from typing import List

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


def get_python_repl_tools() -> List[BaseTool]:
    """PythonREPLTool を返す"""
    try:
        from langchain_experimental.tools import PythonREPLTool
        tool = PythonREPLTool(
            description=(
                "Pythonコードを実行して統計計算・データ分析・可視化を行うツール。"
                "pandas, numpy, scipy, sklearn が利用可能。"
                "入力: 実行するPythonコード文字列\n"
                "注意: 実行結果（stdout）が返される"
            ),
        )
        logger.info("PythonREPLTool: 初期化成功")
        return [tool]
    except ImportError:
        logger.warning(
            "langchain-experimental がインストールされていません: "
            "pip install langchain-experimental"
        )
        return []
    except Exception as e:
        logger.error(f"PythonREPLTool 初期化失敗: {e}")
        return []
