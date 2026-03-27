'use client'

import type { AgentInfo, AgentStatus } from '@/types'

interface Props {
  agents: Record<string, AgentInfo>
}

// エージェントを3列×5行で表示するための順序を定義
const AGENT_ORDER = [
  'aigis',
  'scouter', 'chronos', 'deus',
  'archive', 'valor',   'palette',
  'zenon',   'signal',  'matrix',
  'justice', 'vibe',    'vita',
  'babel',   'mumon',
]

const STATUS_CONFIG: Record<AgentStatus, { dotClass: string; labelColor: string; label: string }> = {
  idle:     { dotClass: 'status-idle',     labelColor: 'text-neon-green/30', label: 'IDLE'     },
  active:   { dotClass: 'status-active',   labelColor: 'text-neon-green',    label: 'ACTIVE'   },
  complete: { dotClass: 'status-complete', labelColor: 'text-[#00aaff]',     label: 'DONE'     },
  error:    { dotClass: 'status-error',    labelColor: 'text-neon-red',      label: 'ERROR'    },
}

function AgentCard({ agent }: { agent: AgentInfo }) {
  const cfg = STATUS_CONFIG[agent.status]
  const isSupervisor = agent.name === 'aigis'

  return (
    <div
      className={`
        relative flex flex-col gap-1 p-2 rounded-sm border transition-all duration-300
        ${agent.status === 'active'
          ? 'border-neon-green/60 bg-neon-dim shadow-neon-sm'
          : agent.status === 'complete'
            ? 'border-[#00aaff]/30 bg-[#001a2e]'
            : 'border-terminal-border bg-terminal-surface'}
        ${isSupervisor ? 'col-span-1 border-neon-green/40' : ''}
      `}
    >
      {/* ステータスドット */}
      <div className="flex items-center justify-between">
        <span className={`inline-block w-2.5 h-2.5 rounded-full shrink-0 ${cfg.dotClass}`} />
        {agent.has_tools && (
          <span className="text-[8px] text-neon-cyan/50 border border-neon-cyan/20 px-1 rounded">
            TOOL
          </span>
        )}
      </div>

      {/* エージェント名 */}
      <div>
        <div
          className={`text-[11px] font-bold tracking-wide truncate leading-tight
            ${agent.status === 'active' ? 'text-glow-sm text-neon-green' : 'text-neon-green/80'}
          `}
        >
          {/* ショートネーム */}
          {agent.display_name.split('（')[0]}
        </div>
        <div className="text-[9px] text-neon-green/40 truncate leading-tight">
          {agent.display_name.match(/（(.+)）/)?.[1] ?? ''}
        </div>
      </div>

      {/* ステータスラベル */}
      <div className={`text-[9px] font-bold tracking-widest ${cfg.labelColor}`}>
        {cfg.label}
      </div>

      {/* アクティブ時のグロー効果 */}
      {agent.status === 'active' && (
        <div className="absolute inset-0 rounded-sm bg-neon-green/5 pointer-events-none animate-pulse" />
      )}
    </div>
  )
}

export function AgentGrid({ agents }: Props) {
  const orderedAgents = AGENT_ORDER
    .map(name => agents[name])
    .filter(Boolean)

  const activeCount   = Object.values(agents).filter(a => a.status === 'active').length
  const completeCount = Object.values(agents).filter(a => a.status === 'complete').length
  const totalCount    = Object.values(agents).length

  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header flex items-center justify-between">
        <span>AGENT GUILD // {totalCount} MEMBERS</span>
        <div className="flex items-center gap-3 text-[9px]">
          {activeCount > 0 && (
            <span className="text-neon-green">
              {activeCount} ACTIVE
            </span>
          )}
          {completeCount > 0 && (
            <span className="text-[#00aaff]">
              {completeCount} DONE
            </span>
          )}
        </div>
      </div>

      {/* エージェントグリッド: 3列 */}
      <div className="flex-1 overflow-auto p-2">
        {totalCount === 0 ? (
          <div className="flex items-center justify-center h-full text-neon-green/30 text-xs">
            接続待機中...
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-1.5">
            {orderedAgents.map(agent => (
              <AgentCard key={agent.name} agent={agent} />
            ))}
          </div>
        )}
      </div>

      {/* フッター: レジェンド */}
      <div className="border-t border-terminal-border px-3 py-1.5 flex items-center gap-4">
        {[
          { cls: 'status-idle',     label: 'IDLE'   },
          { cls: 'status-active',   label: 'ACTIVE' },
          { cls: 'status-complete', label: 'DONE'   },
          { cls: 'status-error',    label: 'ERROR'  },
        ].map(({ cls, label }) => (
          <div key={label} className="flex items-center gap-1">
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${cls}`} />
            <span className="text-[9px] text-neon-green/40">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
