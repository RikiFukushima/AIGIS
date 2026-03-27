"""
A.I.G.I.S. WebSocket ダッシュボードサーバー
FastAPI + WebSocket でリアルタイムに LangGraph の実行状態を配信する

エンドポイント:
  GET  /              ヘルスチェック
  GET  /api/agents    エージェントレジストリ
  GET  /api/metrics   現在のシステムメトリクス
  POST /api/query     クエリ実行トリガー
  POST /api/n8n       n8n Webhook 受信
  WS   /ws            WebSocket ストリーム接続

起動方法:
  uvicorn server:app --reload --port 8000
  # または
  python3 server.py
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set

import psutil
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

# core/ をパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from config import AGENT_REGISTRY, ROUTABLE_AGENTS

logger = logging.getLogger("aigis.server")
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


# ============================================================
# WebSocket コネクションマネージャー
# ============================================================

class ConnectionManager:
    """全 WebSocket クライアントへのブロードキャストを管理する"""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info(f"WS接続: 現在 {len(self._connections)} クライアント")

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)
        logger.info(f"WS切断: 現在 {len(self._connections)} クライアント")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """全クライアントにメッセージを送信する（失敗した接続は自動削除）"""
        if not self._connections:
            return
        payload = json.dumps(message, ensure_ascii=False, default=str)
        dead: Set[WebSocket] = set()
        for ws in list(self._connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        if dead:
            async with self._lock:
                self._connections -= dead

    async def send_to(self, ws: WebSocket, message: Dict[str, Any]) -> None:
        """特定クライアントにのみ送信する（接続直後の初期化データ配信用）"""
        try:
            await ws.send_text(json.dumps(message, ensure_ascii=False, default=str))
        except Exception:
            await self.disconnect(ws)


manager = ConnectionManager()

# ============================================================
# アプリケーション状態
# ============================================================

class AigisAppState:
    """サーバー全体で共有するランタイム状態"""

    def __init__(self) -> None:
        self.is_running: bool = False           # クエリ実行中フラグ
        self.current_query: str = ""
        self.current_session_id: str = ""
        self.active_agent: str = ""
        self.agent_history: list[str] = []
        self._query_lock = asyncio.Lock()       # 同時実行防止

    def reset(self) -> None:
        self.is_running = False
        self.current_query = ""
        self.active_agent = ""
        self.agent_history = []


app_state = AigisAppState()

# ============================================================
# ユーティリティ関数
# ============================================================

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _metrics_snapshot() -> Dict[str, Any]:
    """現在のシステムメトリクスを取得する"""
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)
    return {
        "memory_used_gb": round(mem.used / (1024 ** 3), 2),
        "memory_total_gb": round(mem.total / (1024 ** 3), 2),
        "memory_percent": round(mem.percent, 1),
        "cpu_percent": round(cpu, 1),
        "timestamp": _now(),
    }


def _agent_registry_payload() -> Dict[str, Any]:
    """全エージェントの初期レジストリペイロードを構築する"""
    return {
        "type": "registry",
        "data": {
            "agents": [
                {
                    "name": meta.name,
                    "display_name": meta.display_name,
                    "description": meta.description,
                    "has_tools": meta.has_tools,
                    "tags": meta.tags,
                    "status": "idle",
                }
                for meta in AGENT_REGISTRY.values()
            ]
        },
    }


# ============================================================
# LangGraph 実行 & イベントストリーミング
# ============================================================

ALL_NODE_NAMES: Set[str] = set(AGENT_REGISTRY.keys())


async def _run_graph_streaming(query: str, session_id: str) -> Dict[str, Any]:
    """
    LangGraph グラフを非同期で実行し、各ノードのイベントを WebSocket へストリームする。

    astream_events(version="v2") を使って:
      - on_chain_start  → エージェントの起動通知
      - on_chain_end    → エージェントの完了通知 + 状態更新収集
      - on_chat_model_stream → LLM トークンのリアルタイム配信（推論プロセス可視化）
    """
    # 遅延インポート（Ollamaが起動していない場合のクラッシュを防ぐ）
    from graph import get_graph
    from state import AigisState

    graph = get_graph()
    initial_state: AigisState = {
        "messages": [HumanMessage(content=query)],
        "current_task": "",
        "original_query": query,
        "next_agent": "",
        "responding_agent": "",
        "iteration_count": 0,
        "agent_history": [],
        "collected_data": {},
        "final_answer": None,
    }

    # 全エージェントを idle にリセット
    for name in AGENT_REGISTRY:
        await manager.broadcast({
            "type": "agent_status",
            "data": {
                "agent": name,
                "status": "idle",
                "display_name": AGENT_REGISTRY[name].display_name,
                "timestamp": _now(),
            },
        })

    # 最終出力収集用
    final_messages: list = []
    last_responding_agent: str = "aigis"
    agent_history_collected: list[str] = []
    current_streaming_agent: str = ""
    current_thought_buffer: dict[str, str] = {}  # agent → accumulated tokens

    try:
        async for event in graph.astream_events(initial_state, version="v2"):
            kind: str = event["event"]
            name: str = event.get("name", "")
            metadata: dict = event.get("metadata", {})

            # LangGraph が metadata に現在のノード名を格納する
            node_name: str = metadata.get("langgraph_node", "") or name

            # ─── ノード開始 ─────────────────────────────────────────
            if kind == "on_chain_start" and node_name in ALL_NODE_NAMES:
                app_state.active_agent = node_name
                current_streaming_agent = node_name
                current_thought_buffer[node_name] = ""

                await manager.broadcast({
                    "type": "agent_status",
                    "data": {
                        "agent": node_name,
                        "status": "active",
                        "display_name": AGENT_REGISTRY[node_name].display_name,
                        "timestamp": _now(),
                    },
                })
                await manager.broadcast({
                    "type": "log",
                    "data": {
                        "agent": node_name,
                        "message": f"[{AGENT_REGISTRY[node_name].display_name}] 起動",
                        "level": "info",
                        "timestamp": _now(),
                    },
                })

            # ─── ノード完了 ─────────────────────────────────────────
            elif kind == "on_chain_end" and node_name in ALL_NODE_NAMES:
                output = event.get("data", {}).get("output", {})

                # 最終出力データを収集
                if isinstance(output, dict):
                    if msgs := output.get("messages", []):
                        final_messages.extend(msgs)
                    if ra := output.get("responding_agent"):
                        last_responding_agent = ra
                    if hist := output.get("agent_history", []):
                        agent_history_collected.extend(hist)

                # ストリームが途切れた場合はバッファを flush
                if buf := current_thought_buffer.get(node_name, "").strip():
                    await manager.broadcast({
                        "type": "thought_flush",
                        "data": {
                            "agent": node_name,
                            "display_name": AGENT_REGISTRY[node_name].display_name,
                            "content": buf,
                            "timestamp": _now(),
                        },
                    })
                    current_thought_buffer[node_name] = ""

                await manager.broadcast({
                    "type": "agent_status",
                    "data": {
                        "agent": node_name,
                        "status": "complete",
                        "display_name": AGENT_REGISTRY[node_name].display_name,
                        "timestamp": _now(),
                    },
                })

            # ─── LLM トークンストリーミング（推論プロセス可視化）──────
            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if not chunk:
                    continue

                # content は str または list の場合がある
                content = chunk.content if hasattr(chunk, "content") else ""
                if isinstance(content, list):
                    content = "".join(
                        c.get("text", "") if isinstance(c, dict) else str(c)
                        for c in content
                    )

                if not content:
                    continue

                streaming_node = metadata.get("langgraph_node", current_streaming_agent)
                if streaming_node not in current_thought_buffer:
                    current_thought_buffer[streaming_node] = ""
                current_thought_buffer[streaming_node] += content

                await manager.broadcast({
                    "type": "agent_thought",
                    "data": {
                        "agent": streaming_node,
                        "display_name": AGENT_REGISTRY.get(
                            streaming_node,
                            AGENT_REGISTRY.get("aigis")
                        ).display_name if streaming_node in AGENT_REGISTRY else streaming_node,
                        "token": content,
                        "timestamp": _now(),
                    },
                })

    except Exception as exc:
        logger.exception(f"グラフ実行エラー: {exc}")
        await manager.broadcast({
            "type": "error",
            "data": {"message": str(exc), "timestamp": _now()},
        })
        return {
            "output": f"エラーが発生しました: {exc}",
            "agent": "system",
            "history": agent_history_collected,
        }

    # ─── 最終回答を抽出 ───────────────────────────────────────────
    from langchain_core.messages import AIMessage
    final_output = "回答を生成できませんでした。"
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and str(msg.content).strip():
            final_output = str(msg.content)
            break

    return {
        "output": final_output,
        "agent": last_responding_agent,
        "history": agent_history_collected,
    }


# ============================================================
# バックグラウンドタスク
# ============================================================

async def _metrics_broadcast_loop() -> None:
    """2秒ごとにシステムメトリクスを全クライアントへブロードキャストする"""
    while True:
        await asyncio.sleep(2)
        if manager._connections:
            await manager.broadcast({
                "type": "metrics",
                "data": _metrics_snapshot(),
            })


# ============================================================
# FastAPI アプリケーション
# ============================================================

@asynccontextmanager
async def _lifespan(app: FastAPI):
    """起動時にバックグラウンドタスクを開始する"""
    task = asyncio.create_task(_metrics_broadcast_loop())
    logger.info("A.I.G.I.S. ダッシュボードサーバー起動")
    yield
    task.cancel()
    logger.info("サーバー停止")


app = FastAPI(
    title="A.I.G.I.S. Dashboard API",
    description="15エージェント マルチエージェントシステムのリアルタイム監視",
    version="2.0.0",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では dashboard のオリジンのみに制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── REST エンドポイント ─────────────────────────────────────

@app.get("/")
async def health_check():
    return {
        "status": "online",
        "system": "A.I.G.I.S.",
        "version": "2.0.0",
        "agents": len(AGENT_REGISTRY),
        "ws_clients": len(manager._connections),
        "timestamp": _now(),
    }


@app.get("/api/agents")
async def get_agents():
    """全エージェントのレジストリを返す"""
    return {
        "agents": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "has_tools": m.has_tools,
                "tags": m.tags,
            }
            for m in AGENT_REGISTRY.values()
        ]
    }


@app.get("/api/metrics")
async def get_metrics():
    """現在のシステムメトリクスを返す（HTTPポーリング用）"""
    return _metrics_snapshot()


# ─── クエリ実行エンドポイント ────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    session_id: str = ""


@app.post("/api/query")
async def submit_query(req: QueryRequest):
    """
    クエリを受け付けて LangGraph グラフを非同期実行する。
    実行中の場合は 409 を返す。
    """
    if app_state.is_running:
        raise HTTPException(
            status_code=409,
            detail="現在別のクエリが処理中です。完了後に再試行してください。",
        )

    session_id = req.session_id or str(uuid.uuid4())[:8]

    # 非同期でグラフを実行（レスポンスはすぐ返す）
    asyncio.create_task(_execute_query(req.query, session_id))

    return {
        "status": "accepted",
        "session_id": session_id,
        "message": "クエリを受け付けました。WebSocket でリアルタイム更新を受信してください。",
    }


async def _execute_query(query: str, session_id: str) -> None:
    """クエリ実行の全体フローを制御する"""
    async with app_state._query_lock:
        app_state.is_running = True
        app_state.current_query = query
        app_state.current_session_id = session_id
        app_state.agent_history = []

        await manager.broadcast({
            "type": "query_start",
            "data": {
                "query": query,
                "session_id": session_id,
                "timestamp": _now(),
            },
        })

        try:
            result = await _run_graph_streaming(query, session_id)
        except Exception as exc:
            result = {
                "output": f"実行エラー: {exc}",
                "agent": "system",
                "history": [],
            }

        await manager.broadcast({
            "type": "query_complete",
            "data": {
                "output": result["output"],
                "agent": result["agent"],
                "history": result["history"],
                "session_id": session_id,
                "timestamp": _now(),
            },
        })

        app_state.reset()


# ─── n8n Webhook エンドポイント ──────────────────────────────

class N8nWebhookPayload(BaseModel):
    query: str = ""
    message: str = ""       # n8n が message フィールドを使う場合の互換
    session_id: str = ""
    source: str = "n8n"


@app.post("/api/n8n")
async def n8n_webhook(payload: N8nWebhookPayload):
    """
    n8n からの Webhook を受信してクエリを実行する。
    受信と同時に全クライアントへ通知エフェクトを送信する。
    """
    query = payload.query or payload.message
    if not query:
        raise HTTPException(status_code=422, detail="query または message フィールドが必要です")

    session_id = payload.session_id or f"n8n-{str(uuid.uuid4())[:8]}"

    # n8n 受信通知をブロードキャスト（フロントエンドでエフェクト表示）
    await manager.broadcast({
        "type": "n8n_trigger",
        "data": {
            "query": query,
            "source": payload.source,
            "session_id": session_id,
            "timestamp": _now(),
        },
    })

    if app_state.is_running:
        return {
            "status": "queued",
            "message": "現在処理中のクエリがあるため、完了後に実行されます。",
            "session_id": session_id,
        }

    asyncio.create_task(_execute_query(query, session_id))

    return {
        "status": "accepted",
        "session_id": session_id,
        "source": payload.source,
    }


# ─── WebSocket エンドポイント ────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    WebSocket 接続ハンドラー。
    接続直後に初期化データ（エージェントレジストリ + メトリクス）を送信する。
    その後はサーバーからのプッシュのみ（クライアントからのメッセージも受け付ける）。
    """
    await manager.connect(ws)

    # 接続直後の初期データ送信
    await manager.send_to(ws, _agent_registry_payload())
    await manager.send_to(ws, {
        "type": "metrics",
        "data": _metrics_snapshot(),
    })
    await manager.send_to(ws, {
        "type": "log",
        "data": {
            "agent": "system",
            "message": "A.I.G.I.S. ダッシュボードに接続しました",
            "level": "system",
            "timestamp": _now(),
        },
    })

    try:
        while True:
            # クライアントからのメッセージを受け付ける（ping-pong / コマンド）
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("type") == "query":
                    query = msg.get("query", "").strip()
                    if query and not app_state.is_running:
                        session_id = msg.get("session_id") or str(uuid.uuid4())[:8]
                        asyncio.create_task(_execute_query(query, session_id))
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        await manager.disconnect(ws)
    except Exception as exc:
        logger.warning(f"WebSocket エラー: {exc}")
        await manager.disconnect(ws)


# ============================================================
# 直接起動
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
