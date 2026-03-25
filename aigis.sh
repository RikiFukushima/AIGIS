#!/bin/bash
# A.I.G.I.S. デプロイ・管理スクリプト

set -euo pipefail

# ===== 設定 =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_FILE="${SCRIPT_DIR}/workflows/aigis_main.json"
CONFIG_FILE="${SCRIPT_DIR}/config/aigis_config.json"
BRANCH="claude/aigis-memory-search-EpDjz"
REMOTE="origin"

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:-}"
WORKFLOW_NAME="A.I.G.I.S. - メインワークフロー"

# ===== カラー出力 =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()    { echo -e "${CYAN}[AIGIS]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ===== n8nへのワークフローデプロイ =====
deploy_to_n8n() {
  log_info "n8nへのワークフローデプロイを開始します..."

  if [ -z "$N8N_API_KEY" ]; then
    log_warn "N8N_API_KEY が未設定です。n8nへのデプロイをスキップします。"
    log_warn "設定方法: export N8N_API_KEY=your_api_key"
    return 0
  fi

  if ! command -v curl &>/dev/null; then
    log_error "curl がインストールされていません。"
    return 1
  fi

  if ! command -v jq &>/dev/null; then
    log_warn "jq がインストールされていません。ワークフロー検索をスキップします。"
    _create_workflow
    return 0
  fi

  log_info "既存ワークフローを検索中: ${WORKFLOW_NAME}"
  local response
  response=$(curl -s \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
    "${N8N_URL}/api/v1/workflows" 2>/dev/null || true)

  local workflow_id
  workflow_id=$(echo "$response" | jq -r \
    --arg name "$WORKFLOW_NAME" \
    '.data[] | select(.name == $name) | .id' 2>/dev/null || true)

  if [ -n "$workflow_id" ] && [ "$workflow_id" != "null" ]; then
    log_info "既存ワークフロー (ID: ${workflow_id}) を更新します..."
    curl -s -X PUT \
      -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
      -H "Content-Type: application/json" \
      --data "@${WORKFLOW_FILE}" \
      "${N8N_URL}/api/v1/workflows/${workflow_id}" > /dev/null
    log_success "ワークフローを更新しました (ID: ${workflow_id})"
  else
    _create_workflow
  fi
}

_create_workflow() {
  log_info "新規ワークフローを作成します..."
  local result
  result=$(curl -s -X POST \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
    -H "Content-Type: application/json" \
    --data "@${WORKFLOW_FILE}" \
    "${N8N_URL}/api/v1/workflows" 2>/dev/null || true)
  log_success "ワークフローを作成しました"
  echo "$result" | jq -r '"  -> Workflow ID: " + .id' 2>/dev/null || true
}

# ===== Gitプッシュ（リトライ付き） =====
git_push() {
  log_info "Git: ブランチ '${BRANCH}' にプッシュします..."

  cd "$SCRIPT_DIR"

  # ステージング
  git add -A
  if git diff --cached --quiet; then
    log_info "コミットする変更はありません"
  else
    git commit -m "feat: AIGIS記憶・検索機能の実装

- Window Buffer Memory（過去10回の会話履歴）を追加
- Tavily検索ツールをAI Agentに連結
- system_identity.txtから全知全能の執事プロンプトを定義
- n8nワークフロー(aigis_main.json)にMemory・Searchノードを統合
- aigis.sh デプロイスクリプトを追加

https://claude.ai/code/session_0194o4nZSvwj9HEVK7QYcXHb"
    log_success "コミット完了"
  fi

  # プッシュ（指数バックオフリトライ）
  local attempt=0
  local max_attempts=4
  local wait_time=2

  while [ $attempt -lt $max_attempts ]; do
    if git push -u "$REMOTE" "$BRANCH"; then
      log_success "プッシュ完了: ${REMOTE}/${BRANCH}"
      return 0
    fi

    attempt=$((attempt + 1))
    if [ $attempt -lt $max_attempts ]; then
      log_warn "プッシュ失敗 (試行 ${attempt}/${max_attempts})。${wait_time}秒後にリトライします..."
      sleep "$wait_time"
      wait_time=$((wait_time * 2))
    fi
  done

  log_error "プッシュに失敗しました (${max_attempts}回試行)"
  return 1
}

# ===== コマンド: push =====
cmd_push() {
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║   A.I.G.I.S. デプロイ開始            ║"
  echo "╚══════════════════════════════════════╝"
  echo ""

  deploy_to_n8n
  git_push

  echo ""
  log_success "A.I.G.I.S. のデプロイが完了しました。"
  echo ""
  echo "  次のステップ:"
  echo "  1. n8n で TAVILY_API_KEY を環境変数に設定"
  echo "  2. Anthropic API クレデンシャルを設定"
  echo "  3. ワークフローを有効化 (Activate)"
  echo "  4. Chat Trigger の URL でテスト実行"
  echo ""
}

# ===== コマンド: status =====
cmd_status() {
  log_info "A.I.G.I.S. ステータス確認"
  echo "  Config: ${CONFIG_FILE}"
  echo "  Workflow: ${WORKFLOW_FILE}"
  echo "  N8N URL: ${N8N_URL}"
  echo "  Branch: ${BRANCH}"
  git status --short
}

# ===== ヘルプ =====
cmd_help() {
  echo "使用方法: ./aigis.sh <コマンド>"
  echo ""
  echo "コマンド:"
  echo "  push    ワークフローをn8nにデプロイし、GitHubにプッシュする"
  echo "  status  現在の設定とGitステータスを表示"
  echo "  help    このヘルプを表示"
  echo ""
  echo "環境変数:"
  echo "  N8N_URL       n8nのURL (デフォルト: http://localhost:5678)"
  echo "  N8N_API_KEY   n8n APIキー (n8n Settings > API から取得)"
  echo "  TAVILY_API_KEY Tavily Search APIキー (https://tavily.com)"
}

# ===== エントリーポイント =====
case "${1:-help}" in
  push)   cmd_push   ;;
  status) cmd_status ;;
  help|--help|-h) cmd_help ;;
  *)
    log_error "不明なコマンド: $1"
    cmd_help
    exit 1
    ;;
esac
