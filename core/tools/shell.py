"""
シェルツール - Deus 用
Mac のターミナルコマンドを実行する
"""
from __future__ import annotations

import logging
from typing import List

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


def get_shell_tools() -> List[BaseTool]:
    """ShellTool を返す"""
    try:
        from langchain_community.tools import ShellTool
        tool = ShellTool(
            description=(
                "Mac のターミナルでシェルコマンドを実行するツール。"
                "ファイル操作・システム情報取得・スクリプト実行に使用する。"
                "入力: 実行するシェルコマンド文字列\n"
                "注意: 破壊的な操作（rm -rf 等）は実行前に確認を取ること"
            ),
        )
        logger.info("ShellTool: 初期化成功")
        return [tool]
    except ImportError:
        logger.warning("ShellTool が利用できません")
        return []
    except Exception as e:
        logger.error(f"シェルツール初期化失敗: {e}")
        return []
