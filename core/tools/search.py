"""
検索ツール
DuckDuckGo を使ったWeb検索
"""
from __future__ import annotations

import logging
from typing import List

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


def get_search_tools() -> List[BaseTool]:
    """スカウター用の検索ツールリストを返す"""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun(
            name="web_search",
            description=(
                "インターネットで最新情報を検索するツール。"
                "ニュース、価格、リアルタイム情報の取得に使用する。"
                "入力: 検索クエリ文字列"
            ),
        )
        logger.info("DuckDuckGoSearchRun: 初期化成功")
        return [search]
    except ImportError:
        logger.warning("duckduckgo-search がインストールされていません")
        return []
    except Exception as e:
        logger.error(f"検索ツール初期化失敗: {e}")
        return []
