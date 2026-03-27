#!/bin/bash
# A.I.G.I.S. セットアップスクリプト (Mac M5 Max 128GB 対応)

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
AIGIS_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔═══════════════════════════════════════════════╗"
echo "║   A.I.G.I.S. Core セットアップ (15 Agents)    ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Python バージョン確認
if ! command -v python3 &>/dev/null; then
  echo "[ERROR] python3 が見つかりません"
  exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "[OK] Python: ${PYTHON_VERSION}"

# Ollama 確認
echo ""
echo "── Ollama 確認 ──────────────────────────────────"
if command -v ollama &>/dev/null; then
  echo "[OK] Ollama: インストール済み"

  # llama3.3:70b 確認
  if ollama list 2>/dev/null | grep -q "llama3.3:70b"; then
    echo "[OK] llama3.3:70b: 確認済み"
  else
    echo "[WARN] llama3.3:70b が未ダウンロードです"
    echo "       実行してください: ollama pull llama3.3:70b"
  fi

  # nomic-embed-text 確認 (Archive/RAG用)
  if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
    echo "[OK] nomic-embed-text: 確認済み（RAG用）"
  else
    echo "[INFO] nomic-embed-text (RAG用) が未ダウンロードです"
    echo "       Archiveを使う場合: ollama pull nomic-embed-text"
  fi
else
  echo "[WARN] Ollama が未インストールです"
  echo "       https://ollama.ai からインストール後、以下を実行:"
  echo "       ollama pull llama3.3:70b"
  echo "       ollama pull nomic-embed-text"
fi

# ディレクトリ構造確認・作成
echo ""
echo "── ディレクトリ確認 ─────────────────────────────"
for dir in "${AIGIS_ROOT}/prompts" "${AIGIS_ROOT}/knowledge" "${AIGIS_ROOT}/tools"; do
  if [ -d "$dir" ]; then
    echo "[OK] ${dir}"
  else
    mkdir -p "$dir"
    echo "[作成] ${dir}"
  fi
done

# 仮想環境
echo ""
echo "── 仮想環境 ─────────────────────────────────────"
if [ ! -d "$VENV_DIR" ]; then
  echo "[INFO] 仮想環境を作成中: ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
fi
echo "[OK] 仮想環境: ${VENV_DIR}"

# ライブラリインストール
echo ""
echo "── ライブラリインストール ───────────────────────"
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip
"${VENV_DIR}/bin/pip" install --quiet -r "${SCRIPT_DIR}/requirements.txt"
echo "[OK] インストール完了"

# .env 作成
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
  cat > "${SCRIPT_DIR}/.env" <<'EOF'
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.3:70b
OLLAMA_NUM_CTX=131072
MAX_ITERATIONS=12
LOG_LEVEL=WARNING
EOF
  echo "[OK] .env を作成しました"
fi

# 動作確認テスト
echo ""
echo "── 動作確認 ─────────────────────────────────────"
if "${VENV_DIR}/bin/python3" -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from config import AGENT_REGISTRY, ROUTABLE_AGENTS, PROMPTS_DIR
from state import AigisState
from graph import get_graph
print(f'  エージェント数: {len(AGENT_REGISTRY)}')
print(f'  ルーティング可能: {len(ROUTABLE_AGENTS)} 名')
print(f'  プロンプトDir: {PROMPTS_DIR}')
missing = [n for n in AGENT_REGISTRY if not (PROMPTS_DIR / f\"{n}.txt\").exists()]
if missing:
    print(f'  [WARN] プロンプト未作成: {missing}')
else:
    print(f'  [OK] 全15名のプロンプト確認済み')
get_graph()
print('  [OK] グラフビルド成功')
" 2>/dev/null; then
  echo "[OK] システム動作確認完了"
else
  echo "[WARN] 動作確認でエラーが発生しました（Ollamaが起動していない可能性があります）"
fi

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   セットアップ完了！                          ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "  起動方法:"
echo "    source ${VENV_DIR}/bin/activate"
echo "    python3 main.py \"今日のドル円レートは？\" --pretty"
echo ""
echo "  RAG 知識ベースの構築:"
echo "    ~/Aigis/knowledge/ にドキュメントを配置後:"
echo "    python3 main.py --ingest"
echo ""
echo "  n8n 連携:"
echo "    python3 ~/Aigis/core/main.py \"質問\" 2>/dev/null"
echo ""
