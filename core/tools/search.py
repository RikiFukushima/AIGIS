"""
検索ツール - DuckDuckGo
Scouter・Vibe 用
"""
from __future__ import annotations

import logging
from typing import List

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


def get_search_tools() -> List[BaseTool]:
    """DuckDuckGo 検索ツールを返す"""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        tool = DuckDuckGoSearchRun(
            name="web_search",
            description=(
                "インターネットでリアルタイム情報を検索するツール。"
                "最新ニュース・価格・トレンド・ファクトの取得に使用する。"
                "入力: 検索クエリ（日本語または英語）"
            ),
        )
        logger.info("DuckDuckGoSearchRun: 初期化成功")
        return [tool]
    except ImportError:
        logger.warning("duckduckgo-search がインストールされていません: pip install duckduckgo-search")
        return []
    except Exception as e:
        logger.error(f"検索ツール初期化失敗: {e}")
        return []
