'use client'

import type { SystemMetrics } from '@/types'

interface Props {
  isConnected: boolean
  isRunning: boolean
  metrics: SystemMetrics | null
  currentQuery: string
}

export function SystemHeader({ isConnected, isRunning, metrics, currentQuery }: Props) {
  const now = new Date().toLocaleTimeString('ja-JP', { hour12: false })

  return (
    <header className="flex items-center justify-between px-4 py-2 border-b border-terminal-border bg-terminal-surface select-none">
      {/* 左: タイトル */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          {/* 電源インジケーター */}
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              isConnected ? 'status-active' : 'status-error'
            }`}
          />
          <span className="text-sm font-bold tracking-[0.2em] text-glow">
            A.I.G.I.S.
          </span>
          <span className="text-[10px] text-neon-green/50 tracking-widest hidden sm:inline">
            ADAPTIVE INTEGRATED GENERAL INTELLIGENCE SYSTEM
          </span>
        </div>

        {/* 処理中インジケーター */}
        {isRunning && (
          <div className="flex items-center gap-2 text-[11px]">
            <span className="status-active inline-block w-1.5 h-1.5 rounded-full" />
            <span className="text-neon-green/80 animate-flicker truncate max-w-[240px]">
              PROCESSING: {currentQuery}
            </span>
          </div>
        )}
      </div>

      {/* 右: ステータスバー */}
      <div className="flex items-center gap-6 text-[10px] text-neon-green/60">
        {metrics && (
          <>
            <span>
              CPU <span className="text-neon-green">{metrics.cpu_percent.toFixed(1)}%</span>
            </span>
            <span>
              MEM{' '}
              <span
                className={
                  metrics.memory_percent > 80
                    ? 'text-neon-orange'
                    : 'text-neon-green'
                }
              >
                {metrics.memory_percent.toFixed(1)}%
              </span>
            </span>
            <span>
              {metrics.memory_used_gb.toFixed(1)}
              <span className="text-neon-green/40">/{metrics.memory_total_gb.toFixed(0)} GB</span>
            </span>
          </>
        )}
        <span className="text-neon-green/40 tabular-nums">{now}</span>
        <span
          className={`px-1.5 py-0.5 text-[9px] tracking-widest rounded ${
            isConnected
              ? 'bg-neon-dim text-neon-green border border-neon-green/30'
              : 'bg-red-950 text-neon-red border border-neon-red/30'
          }`}
        >
          {isConnected ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>
    </header>
  )
}
