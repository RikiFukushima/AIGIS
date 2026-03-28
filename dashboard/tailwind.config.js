/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // SF司令室カラーパレット
        terminal: {
          bg:       '#080c08',   // 最深部の黒（微かに緑がかった）
          surface:  '#0d120d',   // パネル背景
          border:   '#1a2e1a',   // ボーダー
          muted:    '#0f1f0f',   // セカンダリ背景
        },
        neon: {
          green:    '#00ff41',   // メインアクセント（Matrix green）
          cyan:     '#00ffff',   // セカンダリアクセント
          orange:   '#ff6600',   // 警告色
          red:      '#ff0040',   // エラー色
          dim:      '#003314',   // 非アクティブ状態
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'monospace'],
      },
      animation: {
        'pulse-neon':   'pulse-neon 1.5s ease-in-out infinite',
        'scan-line':    'scan-line 3s linear infinite',
        'flicker':      'flicker 0.15s infinite',
        'slide-in':     'slide-in 0.3s ease-out',
        'n8n-flash':    'n8n-flash 0.6s ease-out',
        'blink':        'blink 1s step-end infinite',
      },
      keyframes: {
        'pulse-neon': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 8px #00ff41, 0 0 16px #00ff4188' },
          '50%':      { opacity: '0.6', boxShadow: '0 0 4px #00ff41' },
        },
        'scan-line': {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        'flicker': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.8' },
        },
        'slide-in': {
          from: { opacity: '0', transform: 'translateX(-8px)' },
          to:   { opacity: '1', transform: 'translateX(0)' },
        },
        'n8n-flash': {
          '0%':   { opacity: '0', transform: 'translateY(-20px) scale(0.95)' },
          '20%':  { opacity: '1', transform: 'translateY(0) scale(1)' },
          '80%':  { opacity: '1' },
          '100%': { opacity: '0', transform: 'translateY(-10px)' },
        },
        'blink': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        },
      },
      boxShadow: {
        'neon-sm':  '0 0 6px #00ff41',
        'neon-md':  '0 0 12px #00ff41, 0 0 24px #00ff4144',
        'neon-lg':  '0 0 20px #00ff41, 0 0 40px #00ff4166, 0 0 60px #00ff4122',
        'cyan-sm':  '0 0 6px #00ffff',
        'orange-sm':'0 0 6px #ff6600',
        'red-sm':   '0 0 6px #ff0040',
      },
    },
  },
  plugins: [],
}
