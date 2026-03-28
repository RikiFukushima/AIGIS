'use client'

import { useEffect, useRef } from 'react'
import type { LogEntry } from '@/types'

interface Props {
  logs: LogEntry[]
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  } catch {
    return '--:--:--'
  }
}

const TYPE_STYLES: Record<LogEntry['type'], string> = {
  thought: 'log-thought',
  result:  'log-result',
  system:  'log-system',
  error:   'log-error',
  n8n:     'log-n8n',
}

const AGENT_COLORS: Record<string, string> = {
  aigis:      '#00ff41',
  scouter:    '#00ffcc',
  chronos:    '#aaffaa',
  deus:       '#ffcc00',
  archive:    '#88aaff',
  valor:      '#ffaa44',
  palette:    '#ff88cc',
  zenon:      '#ff4488',
  signal:     '#44ffcc',
  matrix:     '#ccff44',
  justice:    '#ffddaa',
  vibe:       '#ff88ff',
  vita:       '#aaffdd',
  babel:      '#44aaff',
  mumon:      '#ddaaff',
  system:     '#00ff4166',
  n8n:        '#ff6600',
}

function LogLine({ entry }: { entry: LogEntry }) {
  const agentColor = AGENT_COLORS[entry.agent] ?? '#00ff41'
  const lineClass = TYPE_STYLES[entry.type] ?? ''

  return (
    <div className={`log-entry ${lineClass} mb-1`}>
      <div className="flex items-start gap-2 text-[11px] leading-relaxed">
        {/* タイムスタンプ */}
        <span className="shrink-0 text-neon-green/30 tabular-nums w-[72px]">
          {formatTime(entry.timestamp)}
        </span>

        {/* エージェント名バッジ */}
        <span
          className="shrink-0 font-bold text-[10px] w-[80px] truncate"
          style={{ color: agentColor, textShadow: `0 0 4px ${agentColor}` }}
        >
          [{entry.agentDisplay.substring(0, 10)}]
        </span>

        {/* コンテンツ */}
        <span
          className={`flex-1 whitespace-pre-wrap break-all leading-relaxed
            ${entry.type === 'result' ? 'text-[#00ffff]' : ''}
            ${entry.type === 'error'  ? 'text-neon-red'  : ''}
          `}
        >
          {entry.content}
          {/* 最後のthoughtエントリにカーソルを表示 */}
          {entry.type === 'thought' && (
            <span className="inline-block w-1.5 h-3 bg-neon-green ml-0.5 animate-blink align-middle" />
          )}
        </span>
      </div>
    </div>
  )
}

export function LogStream({ logs }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const isUserScrolling = useRef(false)
  const scrollTimer = useRef<ReturnType<typeof setTimeout>>()

  // 自動スクロール（ユーザーがスクロール操作中は止める）
  useEffect(() => {
    if (!isUserScrolling.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  const handleScroll = () => {
    isUserScrolling.current = true
    clearTimeout(scrollTimer.current)
    scrollTimer.current = setTimeout(() => {
      isUserScrolling.current = false
    }, 2000)
  }

  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header flex items-center justify-between">
        <span>THOUGHT STREAM // LIVE LOG</span>
        <div className="flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse" />
          <span className="text-[9px] text-neon-green/40">{logs.length} ENTRIES</span>
        </div>
      </div>

      {/* ログ本体 */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-3 space-y-0.5"
        onScroll={handleScroll}
      >
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-neon-green/20">
            <div className="text-3xl">▋</div>
            <div className="text-xs tracking-widest">AWAITING INPUT</div>
            <div className="text-[10px] text-neon-green/10">
              クエリを送信するとここにリアルタイムで推論プロセスが表示されます
            </div>
          </div>
        ) : (
          logs.map(entry => <LogLine key={entry.id} entry={entry} />)
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
