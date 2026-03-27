#!/bin/bash
# A.I.G.I.S. Core セットアップスクリプト

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "╔══════════════════════════════════════╗"
echo "║   A.I.G.I.S. Core セットアップ       ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Python バージョン確認
if ! command -v python3 &>/dev/null; then
  echo "[ERROR] python3 が見つかりません"
  exit 1
fi
echo "[OK] Python: $(python3 --version)"

# Ollama 確認
if command -v ollama &>/dev/null; then
  echo "[OK] Ollama: $(ollama --version 2>/dev/null || echo 'installed')"
  if ! ollama list 2>/dev/null | grep -q "llama3.3:70b"; then
    echo "[WARN] llama3.3:70b が見つかりません。以下を実行してください:"
    echo "  ollama pull llama3.3:70b"
  else
    echo "[OK] llama3.3:70b: 確認済み"
  fi
else
  echo "[WARN] Ollama が見つかりません。https://ollama.ai からインストールしてください"
fi

# 仮想環境作成
if [ ! -d "$VENV_DIR" ]; then
  echo "[INFO] 仮想環境を作成中: ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
fi
echo "[OK] 仮想環境: ${VENV_DIR}"

# ライブラリインストール
echo "[INFO] ライブラリをインストール中..."
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip
"${VENV_DIR}/bin/pip" install --quiet -r "${SCRIPT_DIR}/requirements.txt"
echo "[OK] ライブラリインストール完了"

# .env 作成
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
  cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
  echo "[OK] .env ファイルを作成しました（必要に応じて編集してください）"
fi

echo ""
echo "セットアップ完了！使い方:"
echo "  source .venv/bin/activate"
echo "  python3 main.py \"こんにちは\""
echo ""
