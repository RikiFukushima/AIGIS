'use client'

interface Props {
  alert: { query: string; source: string } | null
}

export function N8nAlert({ alert }: Props) {
  if (!alert) return null

  return (
    <div className="n8n-banner fixed top-12 left-1/2 -translate-x-1/2 z-50
      px-6 py-3 rounded max-w-xl w-full mx-4">
      <div className="flex items-start gap-3">
        {/* アイコン */}
        <div className="text-neon-orange text-xl shrink-0 animate-pulse">⚡</div>

        <div className="flex-1 min-w-0">
          <div className="text-[11px] text-neon-orange/60 tracking-widest mb-1">
            N8N COMMAND RECEIVED // {alert.source.toUpperCase()}
          </div>
          <div className="text-sm text-neon-orange font-bold truncate">
            {alert.query}
          </div>
        </div>

        {/* タグ */}
        <div className="shrink-0 text-[9px] text-neon-orange/50 border border-neon-orange/30
          px-2 py-0.5 rounded tracking-widest">
          AUTO-EXEC
        </div>
      </div>

      {/* プログレスバー（4秒で消える） */}
      <div className="mt-2 h-0.5 bg-neon-orange/20 rounded overflow-hidden">
        <div
          className="h-full bg-neon-orange rounded"
          style={{
            animation: 'shrink-bar 4s linear forwards',
            width: '100%',
          }}
        />
      </div>

      <style jsx>{`
        @keyframes shrink-bar {
          from { width: 100%; }
          to   { width: 0%;   }
        }
      `}</style>
    </div>
  )
}
