"""
シェルツール
Mac のターミナルコマンドを実行する（デウス専用）
"""
from __future__ import annotations

import logging
from typing import List

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

# 安全なコマンドのホワイトリスト（デウスが実行可能なコマンドプレフィックス）
SAFE_COMMAND_PREFIXES = [
    "ls", "pwd", "echo", "date", "whoami", "uname",
    "cat", "head", "tail", "grep", "find", "wc",
    "df", "du", "ps", "top", "uptime",
    "python3", "pip", "brew list", "brew info",
    "git status", "git log", "git diff",
    "open",
]


def get_shell_tools() -> List[BaseTool]:
    """デウス用のシェルツールリストを返す"""
    try:
        from langchain_community.tools import ShellTool

        shell = ShellTool(
            description=(
                "Mac のターミナルコマンドを実行するツール。"
                "ファイル操作、システム情報取得、スクリプト実行に使用する。"
                "入力: 実行するシェルコマンド文字列\n"
                f"推奨コマンド: {', '.join(SAFE_COMMAND_PREFIXES[:10])} など"
            ),
        )
        logger.info("ShellTool: 初期化成功")
        return [shell]
    except ImportError:
        logger.warning("ShellTool が利用できません")
        return []
    except Exception as e:
        logger.error(f"シェルツール初期化失敗: {e}")
        return []
