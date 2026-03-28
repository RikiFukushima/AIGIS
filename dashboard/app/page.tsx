'use client'

import { useEffect, useState } from 'react'
import { useAigisWebSocket } from '@/hooks/useAigisWebSocket'
import { SystemHeader } from '@/components/SystemHeader'
import { MemoryGauge }  from '@/components/MemoryGauge'
import { AgentGrid }    from '@/components/AgentGrid'
import { LogStream }    from '@/components/LogStream'
import { CommandInput } from '@/components/CommandInput'
import { N8nAlert }     from '@/components/N8nAlert'

export default function CommandCenter() {
  const {
    agents, metrics, logs,
    isConnected, isRunning,
    currentQuery, n8nAlert, lastResult,
    sendQuery,
    sendCancel,
  } = useAigisWebSocket()

  // 時刻の更新（ヘッダー用）
  const [, forceRender] = useState(0)
  useEffect(() => {
    const id = setInterval(() => forceRender(n => n + 1), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-terminal-bg">
      {/* ── ヘッダー ── */}
      <SystemHeader
        isConnected={isConnected}
        isRunning={isRunning}
        metrics={metrics}
        currentQuery={currentQuery}
      />

      {/* ── n8n 通知バナー ── */}
      <N8nAlert alert={n8nAlert} />

      {/* ── メインレイアウト ── */}
      <div className="flex-1 flex flex-col overflow-hidden p-2 gap-2">

        {/* 上段: メモリゲージ + エージェントグリッド */}
        <div className="flex gap-2" style={{ height: '42%' }}>
          {/* メモリゲージ: 固定幅 */}
          <div className="w-52 shrink-0">
            <MemoryGauge metrics={metrics} />
          </div>

          {/* エージェントグリッド: 残り幅 */}
          <div className="flex-1">
            <AgentGrid agents={agents} />
          </div>
        </div>

        {/* 下段: ログストリーム */}
        <div className="flex-1 overflow-hidden">
          <LogStream logs={logs} />
        </div>

        {/* コマンド入力 */}
        <div className="shrink-0">
          <CommandInput
            onSubmit={sendQuery}
            onCancel={sendCancel}
            isRunning={isRunning}
            isConnected={isConnected}
          />
        </div>
      </div>

      {/* 最終回答オーバーレイ（完了時にフェードイン） */}
      {lastResult && !isRunning && (
        <ResultOverlay result={lastResult} />
      )}
    </div>
  )
}

// ── 最終回答オーバーレイ ──────────────────────────────────────

interface ResultOverlayProps {
  result: { output: string; agent: string; history: string[] }
}

function ResultOverlay({ result }: ResultOverlayProps) {
  const [visible, setVisible] = useState(true)

  if (!visible) return null

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40
      flex items-end justify-center pb-20 px-4
      animate-[fade-in_0.3s_ease-out]"
      onClick={() => setVisible(false)}
    >
      <div
        className="w-full max-w-3xl panel border-neon-green/40 shadow-neon-md
          max-h-[60vh] overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* ヘッダー */}
        <div className="panel-header flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full status-complete" />
            <span>FINAL RESPONSE // [{result.agent.toUpperCase()}]</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[9px] text-neon-green/40">
              経路: {result.history.join(' → ')}
            </span>
            <button
              onClick={() => setVisible(false)}
              className="text-neon-green/40 hover:text-neon-green transition-colors text-lg leading-none"
            >
              ×
            </button>
          </div>
        </div>

        {/* 回答本文 */}
        <div className="flex-1 overflow-y-auto p-4">
          <p className="text-sm text-[#00ffff] leading-relaxed whitespace-pre-wrap">
            {result.output}
          </p>
        </div>

        <div className="panel-header text-[9px] text-neon-green/30 text-right">
          クリックで閉じる
        </div>
      </div>
    </div>
  )
}
