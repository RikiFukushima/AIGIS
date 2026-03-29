#!/bin/bash
# A.I.G.I.S. ローカル起動スクリプト
# FastAPI バックエンド (port 9999) + Next.js ダッシュボード (port 3333)

set -e

AIGIS_ROOT="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$AIGIS_ROOT/core"
DASHBOARD_DIR="$AIGIS_ROOT/dashboard"

# 色定義
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║  A.I.G.I.S. - Multi-Agent System v2.0   ║"
echo "║  15 Agents • LangGraph • Ollama          ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Ollama の起動確認
echo -e "${CYAN}[1/4] Ollama の確認...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}Ollama が起動していません。先に 'ollama serve' を実行してください。${NC}"
    exit 1
fi
echo "  ✓ Ollama 接続OK"

# Python venv 確認
echo -e "${CYAN}[2/4] Python 仮想環境の確認...${NC}"
if [ ! -d "$CORE_DIR/.venv" ]; then
    echo "  仮想環境を作成中..."
    cd "$CORE_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source "$CORE_DIR/.venv/bin/activate"
fi
echo "  ✓ Python 環境OK"

# FastAPI バックエンド起動
echo -e "${CYAN}[3/4] FastAPI バックエンド起動 (port 9999)...${NC}"
cd "$CORE_DIR"
python3 -m uvicorn server:app --host 0.0.0.0 --port 9999 --log-level info &
BACKEND_PID=$!
echo "  ✓ バックエンド PID: $BACKEND_PID"

# ダッシュボード起動
echo -e "${CYAN}[4/4] Next.js ダッシュボード起動 (port 3333)...${NC}"
cd "$DASHBOARD_DIR"
if [ ! -d "node_modules" ]; then
    echo "  依存関係をインストール中..."
    npm install
fi
npm run dev -- --port 3333 &
FRONTEND_PID=$!
echo "  ✓ ダッシュボード PID: $FRONTEND_PID"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  A.I.G.I.S. 起動完了！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "  ダッシュボード: ${CYAN}http://localhost:3333${NC}"
echo -e "  API:           ${CYAN}http://localhost:9999${NC}"
echo -e "  API Docs:      ${CYAN}http://localhost:9999/docs${NC}"
echo -e "  CLI:           ${CYAN}cd core && source .venv/bin/activate && python3 main.py \"質問\"${NC}"
echo ""
echo -e "  停止するには ${RED}Ctrl+C${NC} を押してください"
echo ""

# Ctrl+C で両方のプロセスを停止
cleanup() {
    echo ""
    echo -e "${CYAN}A.I.G.I.S. を停止中...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}停止完了${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 両プロセスの終了を待機
wait
