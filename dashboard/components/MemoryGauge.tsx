'use client'

import type { SystemMetrics } from '@/types'

interface Props {
  metrics: SystemMetrics | null
}

const RADIUS = 54
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const GAP_DEGREES = 60  // 下部の開口部（度）

// GAP を考慮したアークの長さ
const ARC_FRACTION = (360 - GAP_DEGREES) / 360
const ARC_LENGTH = CIRCUMFERENCE * ARC_FRACTION

function pct2offset(percent: number): number {
  return ARC_LENGTH - (percent / 100) * ARC_LENGTH
}

// パーセントに応じたグラデーションカラー
function gaugeColor(pct: number): string {
  if (pct >= 85) return '#ff0040'
  if (pct >= 70) return '#ff6600'
  return '#00ff41'
}

export function MemoryGauge({ metrics }: Props) {
  const pct     = metrics?.memory_percent ?? 0
  const usedGB  = metrics?.memory_used_gb ?? 0
  const totalGB = metrics?.memory_total_gb ?? 128
  const color   = gaugeColor(pct)

  // SVG の回転: ゲージを下向き開口にするため 90+GAP/2 度回転
  const rotation = 90 + GAP_DEGREES / 2

  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header">MEMORY // 128 GB UNIFIED</div>

      <div className="flex-1 flex flex-col items-center justify-center gap-2 p-4">
        {/* 円形ゲージ */}
        <div className="relative">
          <svg width="160" height="160" viewBox="0 0 160 160">
            <defs>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              {/* グラデーション定義 */}
              <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stopColor={color} stopOpacity="0.6" />
                <stop offset="100%" stopColor={color} stopOpacity="1"   />
              </linearGradient>
            </defs>

            {/* トラック（背景アーク） */}
            <circle
              className="gauge-track"
              cx="80" cy="80" r={RADIUS}
              strokeDasharray={`${ARC_LENGTH} ${CIRCUMFERENCE}`}
              transform={`rotate(${rotation} 80 80)`}
            />

            {/* フィルアーク */}
            <circle
              className="gauge-fill"
              cx="80" cy="80" r={RADIUS}
              stroke="url(#gaugeGrad)"
              strokeDasharray={`${ARC_LENGTH} ${CIRCUMFERENCE}`}
              strokeDashoffset={pct2offset(pct)}
              transform={`rotate(${rotation} 80 80)`}
              filter="url(#glow)"
            />

            {/* 目盛り（25% / 50% / 75%） */}
            {[25, 50, 75].map(tick => {
              const angle = (rotation + (tick / 100) * (360 - GAP_DEGREES)) * (Math.PI / 180)
              const inner = RADIUS - 12
              const outer = RADIUS - 6
              return (
                <line
                  key={tick}
                  x1={80 + inner * Math.cos(angle)}
                  y1={80 + inner * Math.sin(angle)}
                  x2={80 + outer * Math.cos(angle)}
                  y2={80 + outer * Math.sin(angle)}
                  stroke="#1a2e1a"
                  strokeWidth="2"
                />
              )
            })}

            {/* 中央テキスト: パーセント */}
            <text
              x="80" y="72"
              textAnchor="middle"
              fontSize="26"
              fontFamily="JetBrains Mono, monospace"
              fontWeight="700"
              fill={color}
              style={{ filter: `drop-shadow(0 0 6px ${color})` }}
            >
              {pct.toFixed(1)}
            </text>
            <text
              x="80" y="86"
              textAnchor="middle"
              fontSize="10"
              fontFamily="JetBrains Mono, monospace"
              fill={color}
              opacity="0.7"
            >
              %
            </text>

            {/* 使用量 / 合計 */}
            <text
              x="80" y="104"
              textAnchor="middle"
              fontSize="9"
              fontFamily="JetBrains Mono, monospace"
              fill="#00ff41"
              opacity="0.5"
            >
              {usedGB.toFixed(1)} / {totalGB.toFixed(0)} GB
            </text>
          </svg>
        </div>

        {/* ラベル */}
        <div className="text-center space-y-1">
          <div className="text-[10px] text-neon-green/40 tracking-widest">USED</div>
          <div className="text-xl font-bold tabular-nums" style={{ color, textShadow: `0 0 8px ${color}` }}>
            {usedGB.toFixed(2)}<span className="text-xs font-normal opacity-60"> GB</span>
          </div>
        </div>

        {/* ミニバーグラフ（メモリ帯域のビジュアル） */}
        <div className="w-full space-y-1 mt-2">
          {[
            { label: 'USED',  value: pct,         color },
            { label: 'FREE',  value: 100 - pct,   color: '#1a2e1a' },
          ].map(bar => (
            <div key={bar.label} className="flex items-center gap-2">
              <span className="text-[9px] text-neon-green/40 w-8 shrink-0">{bar.label}</span>
              <div className="flex-1 h-1 bg-terminal-border rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000"
                  style={{
                    width: `${bar.value}%`,
                    background: bar.color,
                    boxShadow: bar.label === 'USED' ? `0 0 4px ${color}` : undefined,
                  }}
                />
              </div>
              <span className="text-[9px] text-neon-green/40 w-8 text-right tabular-nums">
                {bar.value.toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
