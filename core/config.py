"""
A.I.G.I.S. 設定・エージェントレジストリ
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ===== モデル設定 =====
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.3:70b")
MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))

# ===== パス設定 =====
CORE_DIR = Path(__file__).parent
PROMPTS_DIR = CORE_DIR / "prompts"


@dataclass
class AgentMeta:
    """エージェントのメタ情報"""
    name: str           # 内部キー (ルーティングに使用)
    display_name: str   # 表示名（日本語）
    description: str    # 専門分野の説明
    has_tools: bool = False
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


# ===== エージェントレジストリ =====
# Priority 1: 実装済み
# Priority 2: スタブ（プロンプトのみ定義、ノードは汎用実装）

AGENT_REGISTRY: Dict[str, AgentMeta] = {
    # --- Priority 1: 実装済み ---
    "aigis": AgentMeta(
        name="aigis",
        display_name="アイギス",
        description="全エージェントを統括するスーパーバイザー兼執事。タスクを分析し最適な専門家へ振り分ける",
        tags=["supervisor", "router"],
    ),
    "scouter": AgentMeta(
        name="scouter",
        display_name="スカウター",
        description="Web検索・情報収集の専門家。最新情報やファクトの取得を担当する",
        has_tools=True,
        tags=["search", "web", "realtime"],
    ),

    # --- Priority 2: スタブ（順次実装予定） ---
    "deus": AgentMeta(
        name="deus",
        display_name="デウス",
        description="Macのシェルコマンド実行・システム操作の専門家",
        has_tools=True,
        tags=["shell", "system", "execution"],
    ),
    "kronos": AgentMeta(
        name="kronos",
        display_name="クロノス",
        description="時間管理・スケジューリング・タイムライン分析の専門家",
        tags=["time", "schedule", "calendar"],
    ),
    "archive": AgentMeta(
        name="archive",
        display_name="アーカイブ",
        description="知識ベース管理・過去情報の検索と整理の専門家",
        tags=["memory", "knowledge", "retrieval"],
    ),
    "logos": AgentMeta(
        name="logos",
        display_name="ロゴス",
        description="論理分析・推論・構造化思考の専門家",
        tags=["analysis", "logic", "reasoning"],
    ),
    "hephaestus": AgentMeta(
        name="hephaestus",
        display_name="ヘファイストス",
        description="コード生成・ソフトウェアエンジニアリングの専門家",
        tags=["code", "engineering", "programming"],
    ),
    "hermes": AgentMeta(
        name="hermes",
        display_name="ヘルメス",
        description="翻訳・フォーマット変換・出力整形の専門家",
        tags=["translation", "formatting", "output"],
    ),
    "athena": AgentMeta(
        name="athena",
        display_name="アテナ",
        description="戦略立案・計画設計・意思決定支援の専門家",
        tags=["strategy", "planning", "decision"],
    ),
    "muse": AgentMeta(
        name="muse",
        display_name="ミューズ",
        description="クリエイティブライティング・アイデア発想の専門家",
        tags=["creative", "writing", "ideation"],
    ),
    "argos": AgentMeta(
        name="argos",
        display_name="アルゴス",
        description="監視・異常検知・アラート管理の専門家",
        tags=["monitoring", "alert", "vigilance"],
    ),
    "sophia": AgentMeta(
        name="sophia",
        display_name="ソフィア",
        description="深層推論・哲学的考察・複雑問題の解決専門家",
        tags=["deep_reasoning", "philosophy", "complex"],
    ),
    "gaia": AgentMeta(
        name="gaia",
        display_name="ガイア",
        description="データ統合・複数情報源の集約と要約の専門家",
        tags=["synthesis", "aggregation", "summary"],
    ),
    "nemesis": AgentMeta(
        name="nemesis",
        display_name="ネメシス",
        description="ファクトチェック・批判的検証・品質保証の専門家",
        tags=["fact_check", "critique", "qa"],
    ),
    "prometheus": AgentMeta(
        name="prometheus",
        display_name="プロメテウス",
        description="学習・リサーチ・新技術調査の専門家",
        tags=["learning", "research", "discovery"],
    ),
}

# ルーティング可能なエージェント一覧（aigisSupervisor自身を除く）
ROUTABLE_AGENTS: List[str] = [
    k for k, v in AGENT_REGISTRY.items()
    if k != "aigis" and v.enabled
]
