import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'A.I.G.I.S. COMMAND CENTER',
  description: '15-Agent LangGraph Monitoring Dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <body className="h-screen overflow-hidden bg-terminal-bg text-neon-green font-mono">
        {children}
      </body>
    </html>
  )
}
