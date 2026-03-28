// A.I.G.I.S. ダッシュボード 型定義

export type AgentStatus = 'idle' | 'active' | 'complete' | 'error'

export interface AgentInfo {
  name: string
  display_name: string
  description: string
  has_tools: boolean
  tags: string[]
  status: AgentStatus
}

export interface LogEntry {
  id: string
  timestamp: string
  agent: string
  agentDisplay: string
  content: string
  type: 'thought' | 'result' | 'system' | 'error' | 'n8n'
}

export interface SystemMetrics {
  memory_used_gb: number
  memory_total_gb: number
  memory_percent: number
  cpu_percent: number
  timestamp: string
}

export interface QueryResult {
  output: string
  agent: string
  history: string[]
  session_id: string
  timestamp: string
}

// WebSocket メッセージ型
export type WsMessage =
  | { type: 'registry';       data: { agents: AgentInfo[] } }
  | { type: 'agent_status';   data: { agent: string; status: AgentStatus; display_name: string; timestamp: string } }
  | { type: 'agent_thought';  data: { agent: string; display_name: string; token: string; timestamp: string } }
  | { type: 'thought_flush';  data: { agent: string; display_name: string; content: string; timestamp: string } }
  | { type: 'metrics';        data: SystemMetrics }
  | { type: 'n8n_trigger';    data: { query: string; source: string; session_id: string; timestamp: string } }
  | { type: 'query_start';    data: { query: string; session_id: string; timestamp: string } }
  | { type: 'query_complete'; data: QueryResult }
  | { type: 'log';            data: { agent: string; message: string; level: string; timestamp: string } }
  | { type: 'error';          data: { message: string; timestamp: string } }
