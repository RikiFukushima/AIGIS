"""
RAG ツール - Archive 用
ChromaDB を使ったローカルベクターストア検索
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from langchain_core.tools import BaseTool

from config import KNOWLEDGE_DIR

logger = logging.getLogger(__name__)

# ChromaDB の永続化パス
CHROMA_PERSIST_DIR = str(KNOWLEDGE_DIR / "chroma_db")
COLLECTION_NAME = "aigis_knowledge"


def get_rag_tools() -> List[BaseTool]:
    """
    ChromaDB ベクターストア検索ツールを返す。
    ChromaDB が未初期化 or インポートエラーの場合は空リストを返す。
    """
    try:
        import chromadb
        from langchain_community.vectorstores import Chroma
        from langchain_ollama import OllamaEmbeddings
        from langchain.tools.retriever import create_retriever_tool

        # ChromaDB クライアント初期化
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

        # コレクション存在確認
        existing = [c.name for c in client.list_collections()]
        if COLLECTION_NAME not in existing:
            logger.info(
                f"ChromaDB コレクション '{COLLECTION_NAME}' が未作成です。"
                f"ドキュメントを {KNOWLEDGE_DIR} に配置後、ingest スクリプトを実行してください。"
            )
            return []

        # Embeddings (Ollama の nomic-embed-text を使用)
        embeddings = OllamaEmbeddings(model="nomic-embed-text")

        # ベクターストア接続
        vectorstore = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )

        retriever = vectorstore.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance: 多様性を確保
            search_kwargs={"k": 5, "fetch_k": 20},
        )

        tool = create_retriever_tool(
            retriever,
            name="knowledge_search",
            description=(
                "~/Aigis/knowledge/ に蓄積されたローカル知識ベースを検索するツール。"
                "過去のドキュメント・メモ・資料から関連情報を取得する。"
                "入力: 検索クエリ文字列"
            ),
        )

        logger.info(f"RAGツール: ChromaDB '{COLLECTION_NAME}' に接続成功")
        return [tool]

    except ImportError:
        logger.warning("chromadb または関連ライブラリがインストールされていません: pip install chromadb")
        return []
    except Exception as e:
        logger.warning(f"RAGツール初期化スキップ（ChromaDB未準備）: {e}")
        return []


def ingest_documents(source_dir: Path | None = None) -> int:
    """
    ~/Aigis/knowledge/ 内のドキュメントを ChromaDB に取り込む。

    対応フォーマット: .txt, .md, .pdf
    戻り値: 取り込んだチャンク数
    """
    try:
        import chromadb
        from langchain_community.document_loaders import (
            DirectoryLoader,
            TextLoader,
            UnstructuredMarkdownLoader,
        )
        from langchain_community.vectorstores import Chroma
        from langchain_ollama import OllamaEmbeddings
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        target_dir = source_dir or KNOWLEDGE_DIR
        if not target_dir.exists():
            logger.error(f"ディレクトリが存在しません: {target_dir}")
            return 0

        # ドキュメント読み込み
        loader = DirectoryLoader(
            str(target_dir),
            glob="**/*.{txt,md}",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            recursive=True,
            exclude=["**/chroma_db/**"],
        )
        docs = loader.load()
        if not docs:
            logger.warning(f"ドキュメントが見つかりません: {target_dir}")
            return 0

        # テキスト分割
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        chunks = splitter.split_documents(docs)

        # Embeddings & 保存
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
            collection_name=COLLECTION_NAME,
        )

        logger.info(f"取り込み完了: {len(docs)} ドキュメント → {len(chunks)} チャンク")
        return len(chunks)

    except Exception as e:
        logger.error(f"ドキュメント取り込みエラー: {e}")
        return 0
