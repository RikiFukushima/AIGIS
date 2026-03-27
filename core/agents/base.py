"""
A.I.G.I.S. ベースエージェント
全エージェント共通のユーティリティ
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from langchain_core.messages import AIMessage, BaseMessage
from langchain_ollama import ChatOllama

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_NUM_CTX, PROMPTS_DIR

logger = logging.getLogger(__name__)


def load_prompt(agent_name: str) -> str:
    """
    ~/Aigis/prompts/{agent_name}.txt を読み込む。
    見つからなければデフォルト文を返す。
    """
    prompt_path = PROMPTS_DIR / f"{agent_name}.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    logger.warning(f"プロンプトファイルが見つかりません: {prompt_path}")
    return f"あなたは {agent_name} という名の専門エージェントです。与えられたタスクに誠実に取り組んでください。"


def build_llm(temperature: float = 0.7, num_ctx: int | None = None) -> ChatOllama:
    """
    Ollama LLM インスタンスを構築する。
    128GB RAM を活かし num_ctx を最大設定。
    """
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        num_ctx=num_ctx or OLLAMA_NUM_CTX,
    )


def extract_last_ai_content(messages: List[BaseMessage]) -> Optional[str]:
    """メッセージリストから最後のAIメッセージのテキストを取得する"""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return None
