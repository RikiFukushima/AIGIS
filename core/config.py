"""
A.I.G.I.S. 設定・エージェントレジストリ
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# プロジェクトルート = core/ の親ディレクトリ
AIGIS_ROOT = Path(__file__).parent.parent
load_dotenv(AIGIS_ROOT / "core" / ".env")

# ===== パス設定 =====
CORE_DIR = AIGIS_ROOT / "core"
PROMPTS_DIR = AIGIS_ROOT / "prompts"
KNOWLEDGE_DIR = AIGIS_ROOT / "knowledge"
TOOLS_DIR = AIGIS_ROOT / "tools"

# ===== モデル設定 =====
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.3:70b")

# 128GB RAM を活かした最大コンテキストウィンドウ
OLLAMA_NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "131072"))  # 128k tokens

MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "12"))


@dataclass
class AgentMeta:
    name: str
    display_name: str
    description: str
    has_tools: bool = False
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


# ===== 精鋭15名のレジストリ =====
AGENT_REGISTRY: Dict[str, AgentMeta] = {
    "aigis": AgentMeta(
        name="aigis",
        display_name="AIGIS（執事）",
        description="全体の司令塔・ルーター。タスクを分析し最適な専門家へ振り分ける",
        tags=["supervisor", "router"],
    ),
    "scouter": AgentMeta(
        name="scouter",
        display_name="Scouter（探査官）",
        description="ネット検索・情報収集・リアルタイムデータ取得",
        has_tools=True,
        tags=["search", "web", "realtime"],
    ),
    "chronos": AgentMeta(
        name="chronos",
        display_name="Chronos（軍師）",
        description="戦略立案・深層思考・多段階シナリオ計画",
        tags=["strategy", "deep_thinking", "planning"],
    ),
    "deus": AgentMeta(
        name="deus",
        display_name="Deus（工機官）",
        description="システム開発・自動化・ファイル操作・シェル実行",
        has_tools=True,
        tags=["shell", "automation", "code"],
    ),
    "archive": AgentMeta(
        name="archive",
        display_name="Archive（記録官）",
        description="ローカルRAG・過去データ・知識ベース検索（ChromaDB）",
        has_tools=True,
        tags=["rag", "memory", "knowledge", "chromadb"],
    ),
    "valor": AgentMeta(
        name="valor",
        display_name="Valor（鑑定士）",
        description="財務分析・為替・投資判断・ポートフォリオ評価",
        tags=["finance", "investment", "forex"],
    ),
    "palette": AgentMeta(
        name="palette",
        display_name="Palette（描画師）",
        description="画像生成プロンプト作成・UIデザイン指示・ビジュアル制作",
        tags=["image", "design", "ui", "visual"],
    ),
    "zenon": AgentMeta(
        name="zenon",
        display_name="Zenon（防壁）",
        description="セキュリティ分析・プライバシー監視・脅威評価",
        tags=["security", "privacy", "threat"],
    ),
    "signal": AgentMeta(
        name="signal",
        display_name="Signal（外交官）",
        description="交渉・代筆・ビジネスコミュニケーション・多言語文書作成",
        tags=["communication", "writing", "negotiation"],
    ),
    "matrix": AgentMeta(
        name="matrix",
        display_name="Matrix（解析官）",
        description="統計解析・大規模データ演算・Pythonコード実行",
        has_tools=True,
        tags=["statistics", "data", "python", "analysis"],
    ),
    "justice": AgentMeta(
        name="justice",
        display_name="Justice（法務官）",
        description="契約・規約・法的リスクチェック・コンプライアンス評価",
        tags=["legal", "contract", "compliance"],
    ),
    "vibe": AgentMeta(
        name="vibe",
        display_name="Vibe（予言者）",
        description="SNSトレンド分析・感情分析・バズ予測",
        has_tools=True,
        tags=["sns", "trend", "sentiment", "social"],
    ),
    "vita": AgentMeta(
        name="vita",
        display_name="Vita（調律師）",
        description="健康管理・生産性最適化・ライフスタイル設計",
        tags=["health", "productivity", "lifestyle"],
    ),
    "babel": AgentMeta(
        name="babel",
        display_name="Babel（翻訳官）",
        description="超高精度翻訳・異文化接続・多言語コンテンツ作成",
        tags=["translation", "localization", "multilingual"],
    ),
    "mumon": AgentMeta(
        name="mumon",
        display_name="Mumon（禅師）",
        description="メンタルケア・思考の整理・内省・哲学的対話",
        tags=["mental", "mindfulness", "philosophy", "reflection"],
    ),
}

# ルーティング可能なエージェント（aigisを除く14名）
ROUTABLE_AGENTS: List[str] = [
    k for k, v in AGENT_REGISTRY.items()
    if k != "aigis" and v.enabled
]
