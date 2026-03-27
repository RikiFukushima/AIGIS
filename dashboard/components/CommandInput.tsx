'use client'

import { KeyboardEvent, useRef, useState } from 'react'

interface Props {
  onSubmit: (query: string) => void
  isRunning: boolean
  isConnected: boolean
}

const QUICK_COMMANDS = [
  '今日のドル円相場を教えて',
  'Pythonでクイックソートを実装して',
  '現在のシステム状態を確認して',
]

export function CommandInput({ onSubmit, isRunning, isConnected }: Props) {
  const [value, setValue] = useState('')
  const [history, setHistory] = useState<string[]>([])
  const [historyIdx, setHistoryIdx] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = () => {
    const q = value.trim()
    if (!q || isRunning || !isConnected) return
    onSubmit(q)
    setHistory(prev => [q, ...prev.slice(0, 49)])
    setValue('')
    setHistoryIdx(-1)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit()
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      const idx = Math.min(historyIdx + 1, history.length - 1)
      setHistoryIdx(idx)
      if (history[idx]) setValue(history[idx])
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      const idx = Math.max(historyIdx - 1, -1)
      setHistoryIdx(idx)
      setValue(idx === -1 ? '' : history[idx])
    }
  }

  return (
    <div className="panel">
      {/* クイックコマンド */}
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-terminal-border overflow-x-auto">
        <span className="text-[9px] text-neon-green/30 shrink-0 tracking-widest">QUICK</span>
        {QUICK_COMMANDS.map(cmd => (
          <button
            key={cmd}
            onClick={() => {
              if (!isRunning && isConnected) {
                onSubmit(cmd)
                setHistory(prev => [cmd, ...prev.slice(0, 49)])
              }
            }}
            disabled={isRunning || !isConnected}
            className="shrink-0 text-[10px] text-neon-green/50 hover:text-neon-green
              border border-terminal-border hover:border-neon-green/40
              px-2 py-0.5 rounded transition-all duration-150
              disabled:opacity-30 disabled:cursor-not-allowed"
          >
            {cmd.slice(0, 20)}{cmd.length > 20 ? '…' : ''}
          </button>
        ))}
      </div>

      {/* 入力行 */}
      <div
        className="flex items-center gap-3 px-3 py-2 cursor-text"
        onClick={() => inputRef.current?.focus()}
      >
        {/* プロンプト記号 */}
        <span
          className={`text-sm font-bold shrink-0 transition-colors
            ${isRunning ? 'text-neon-orange animate-pulse' :
              !isConnected ? 'text-neon-red' : 'text-neon-green text-glow-sm'}`}
        >
          {isRunning ? '⟳' : !isConnected ? '✗' : '▶'}
        </span>

        {/* 入力フィールド */}
        <input
          ref={inputRef}
          type="text"
          className="command-input"
          placeholder={
            !isConnected ? 'サーバーに接続中...' :
            isRunning    ? '処理中です。完了までお待ちください...' :
                           'A.I.G.I.S. に命令を入力 (↑↓で履歴、Enterで送信)'
          }
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isRunning || !isConnected}
          autoFocus
          spellCheck={false}
          autoComplete="off"
        />

        {/* 文字数 */}
        {value.length > 0 && (
          <span className="text-[10px] text-neon-green/30 shrink-0 tabular-nums">
            {value.length}
          </span>
        )}

        {/* 送信ボタン */}
        <button
          onClick={handleSubmit}
          disabled={isRunning || !isConnected || !value.trim()}
          className="shrink-0 text-[10px] tracking-widest px-3 py-1
            border border-neon-green/30 text-neon-green/60
            hover:border-neon-green hover:text-neon-green hover:shadow-neon-sm
            disabled:opacity-20 disabled:cursor-not-allowed
            transition-all duration-150 rounded-sm"
        >
          SEND
        </button>
      </div>
    </div>
  )
}
