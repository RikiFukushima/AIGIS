'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import type { AgentInfo, AgentStatus, LogEntry, SystemMetrics, WsMessage } from '@/types'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:9999/ws'
const MAX_LOG_ENTRIES = 500
const RECONNECT_DELAY_MS = 3000

interface AigisWsState {
  agents: Record<string, AgentInfo>
  metrics: SystemMetrics | null
  logs: LogEntry[]
  isConnected: boolean
  isRunning: boolean
  currentQuery: string
  n8nAlert: { query: string; source: string } | null
  lastResult: { output: string; agent: string; history: string[] } | null
}

export function useAigisWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const logIdCounter = useRef(0)
  const thoughtBuffers = useRef<Record<string, string>>({})

  const [state, setState] = useState<AigisWsState>({
    agents: {},
    metrics: null,
    logs: [],
    isConnected: false,
    isRunning: false,
    currentQuery: '',
    n8nAlert: null,
    lastResult: null,
  })

  // ── ログ追加ヘルパー ──────────────────────────────────────
  const addLog = useCallback((entry: Omit<LogEntry, 'id'>) => {
    logIdCounter.current += 1
    const id = `log-${logIdCounter.current}`
    setState(prev => ({
      ...prev,
      logs: [...prev.logs.slice(-MAX_LOG_ENTRIES + 1), { ...entry, id }],
    }))
  }, [])

  // ── エージェントのステータス更新 ─────────────────────────
  const updateAgentStatus = useCallback((name: string, status: AgentStatus) => {
    setState(prev => {
      if (!prev.agents[name]) return prev
      return {
        ...prev,
        agents: {
          ...prev.agents,
          [name]: { ...prev.agents[name], status },
        },
      }
    })
  }, [])

  // ── WS メッセージハンドラー ──────────────────────────────
  const handleMessage = useCallback((msg: WsMessage) => {
    switch (msg.type) {

      case 'registry': {
        const agentMap: Record<string, AgentInfo> = {}
        for (const a of msg.data.agents) {
          agentMap[a.name] = { ...a, status: 'idle' }
        }
        setState(prev => ({ ...prev, agents: agentMap }))
        break
      }

      case 'agent_status': {
        const { agent, status, display_name } = msg.data
        updateAgentStatus(agent, status)

        if (status === 'active') {
          addLog({
            agent,
            agentDisplay: display_name,
            content: `▶ ${display_name} — 起動`,
            type: 'system',
            timestamp: msg.data.timestamp,
          })
          // 新エージェント起動時にバッファをリセット
          thoughtBuffers.current[agent] = ''
        } else if (status === 'complete') {
          addLog({
            agent,
            agentDisplay: display_name,
            content: `✓ ${display_name} — 完了`,
            type: 'system',
            timestamp: msg.data.timestamp,
          })
        }
        break
      }

      case 'agent_thought': {
        const { agent, display_name, token } = msg.data
        // トークンをバッファに蓄積（UIはトークン単位でログを更新）
        if (thoughtBuffers.current[agent] === undefined) {
          thoughtBuffers.current[agent] = ''
          // 新しいthoughtエントリをログに追加（後続トークンは同エントリを更新）
          addLog({
            agent,
            agentDisplay: display_name,
            content: token,
            type: 'thought',
            timestamp: msg.data.timestamp,
          })
        } else {
          // 既存エントリの最後のthoughtを更新
          setState(prev => {
            const logs = [...prev.logs]
            // 同じエージェントの最後のthoughtエントリを探す
            const idx = logs.findLastIndex(
              l => l.agent === agent && l.type === 'thought'
            )
            if (idx !== -1) {
              logs[idx] = { ...logs[idx], content: logs[idx].content + token }
              return { ...prev, logs }
            }
            return prev
          })
        }
        thoughtBuffers.current[agent] = (thoughtBuffers.current[agent] ?? '') + token
        break
      }

      case 'thought_flush': {
        const { agent, display_name, content } = msg.data
        thoughtBuffers.current[agent] = ''
        // バッファのリセット（flush後は次のエージェントで新エントリを作る）
        setState(prev => {
          const logs = [...prev.logs]
          const idx = logs.findLastIndex(l => l.agent === agent && l.type === 'thought')
          if (idx !== -1) {
            logs[idx] = { ...logs[idx], content }
          }
          return { ...prev, logs }
        })
        break
      }

      case 'metrics': {
        setState(prev => ({ ...prev, metrics: msg.data }))
        break
      }

      case 'query_start': {
        thoughtBuffers.current = {}
        setState(prev => ({
          ...prev,
          isRunning: true,
          currentQuery: msg.data.query,
          lastResult: null,
        }))
        addLog({
          agent: 'system',
          agentDisplay: 'SYSTEM',
          content: `━━ クエリ受信 [${msg.data.session_id}]: "${msg.data.query}"`,
          type: 'system',
          timestamp: msg.data.timestamp,
        })
        break
      }

      case 'query_complete': {
        setState(prev => ({
          ...prev,
          isRunning: false,
          currentQuery: '',
          lastResult: {
            output: msg.data.output,
            agent: msg.data.agent,
            history: msg.data.history,
          },
        }))
        addLog({
          agent: msg.data.agent,
          agentDisplay: '最終回答',
          content: msg.data.output,
          type: 'result',
          timestamp: msg.data.timestamp,
        })
        // 全エージェントをidleに戻す
        setState(prev => {
          const agents = { ...prev.agents }
          for (const k of Object.keys(agents)) {
            if (agents[k].status === 'active' || agents[k].status === 'complete') {
              agents[k] = { ...agents[k], status: 'idle' }
            }
          }
          return { ...prev, agents }
        })
        break
      }

      case 'n8n_trigger': {
        const { query, source } = msg.data
        setState(prev => ({ ...prev, n8nAlert: { query, source } }))
        addLog({
          agent: 'n8n',
          agentDisplay: 'n8n',
          content: `⚡ n8n から命令受信: "${query}"`,
          type: 'n8n',
          timestamp: msg.data.timestamp,
        })
        // 4秒後にアラートを消す
        setTimeout(() => {
          setState(prev => ({ ...prev, n8nAlert: null }))
        }, 4000)
        break
      }

      case 'log': {
        addLog({
          agent: msg.data.agent,
          agentDisplay: msg.data.agent.toUpperCase(),
          content: msg.data.message,
          type: 'system',
          timestamp: msg.data.timestamp,
        })
        break
      }

      case 'error': {
        addLog({
          agent: 'system',
          agentDisplay: 'ERROR',
          content: `⚠ ${msg.data.message}`,
          type: 'error',
          timestamp: msg.data.timestamp,
        })
        break
      }
    }
  }, [addLog, updateAgentStatus])

  // ── WebSocket 接続 ────────────────────────────────────────
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setState(prev => ({ ...prev, isConnected: true }))
    }

    ws.onmessage = (e: MessageEvent) => {
      try {
        const msg = JSON.parse(e.data) as WsMessage
        handleMessage(msg)
      } catch { /* ignore malformed */ }
    }

    ws.onerror = () => {
      setState(prev => ({ ...prev, isConnected: false }))
    }

    ws.onclose = () => {
      setState(prev => ({ ...prev, isConnected: false }))
      wsRef.current = null
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
    }
  }, [handleMessage])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  // ── クエリ送信 ────────────────────────────────────────────
  const sendQuery = useCallback((query: string) => {
    if (!query.trim()) return
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'query', query: query.trim() }))
    }
  }, [])

  // ── キャンセル送信 ──────────────────────────────────────────
  const sendCancel = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'cancel' }))
    }
  }, [])

  return { ...state, sendQuery, sendCancel }
}
