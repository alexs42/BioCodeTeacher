/**
 * API service for communicating with the BioCodeTeacher backend.
 */

const API_BASE = '/api'
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const WS_BASE = `${WS_PROTOCOL}//${window.location.host}/api`

// Types
export interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  language?: string
  children?: FileNode[]
}

export interface RepoLoadResponse {
  success: boolean
  repo_id: string
  root_path: string
  file_tree: FileNode
  file_count: number
  message?: string
  has_cached_analysis?: boolean
}

export interface FileContentResponse {
  path: string
  content: string
  language: string
  line_count: number
}

// Repository API
export async function loadLocalRepo(path: string): Promise<RepoLoadResponse> {
  if (!path || !path.trim()) {
    throw new Error('Repository path is required')
  }

  const response = await fetch(`${API_BASE}/repos/load`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: path.trim() }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to load repository')
  }

  return response.json()
}

export async function loadGithubRepo(
  githubUrl: string,
  githubToken?: string
): Promise<RepoLoadResponse> {
  const response = await fetch(`${API_BASE}/repos/load`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ github_url: githubUrl, github_token: githubToken }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to clone repository')
  }

  return response.json()
}

// Directory browse API
export interface DirectoryEntry {
  name: string
  path: string
}

export interface BrowseResponse {
  current: string
  parent: string | null
  directories: DirectoryEntry[]
}

export async function browseDirectory(path: string = ''): Promise<BrowseResponse> {
  const params = new URLSearchParams({ path })
  const response = await fetch(`${API_BASE}/repos/browse?${params}`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to browse directory')
  }

  return response.json()
}

// Architecture file context API
export interface FileContextResponse {
  found: boolean
  file?: string
  role?: string
  imports?: { path: string; role: string | null }[]
  imported_by?: { path: string; role: string }[]
  patterns?: string[]
}

export async function getFileContext(
  repoId: string,
  filePath: string
): Promise<FileContextResponse> {
  const params = new URLSearchParams({ file_path: filePath })
  const response = await fetch(`${API_BASE}/explain/file-context/${repoId}?${params}`)
  if (!response.ok) return { found: false }
  return response.json()
}

// File API
export async function getFileContent(
  repoId: string,
  filePath: string
): Promise<FileContentResponse> {
  const params = new URLSearchParams({ repo_id: repoId, file_path: filePath })
  const response = await fetch(`${API_BASE}/files/content?${params}`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to read file')
  }

  return response.json()
}

// WebSocket for streaming explanations
export type StreamMessageType = 'start' | 'chunk' | 'end' | 'error' | 'phase' | 'file_analyzed'

export interface StreamMessage {
  type: StreamMessageType
  content?: string
  metadata?: Record<string, unknown>
}

export function createExplanationStream(
  onMessage: (msg: StreamMessage) => void,
  onError: (error: Error) => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/explain/stream`)

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data) as StreamMessage
      onMessage(message)
    } catch (e) {
      onError(new Error('Failed to parse message'))
    }
  }

  ws.onerror = () => {
    onError(new Error('WebSocket connection error'))
  }

  return ws
}

export function createChatStream(
  onMessage: (msg: StreamMessage) => void,
  onError: (error: Error) => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/chat/stream`)

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data) as StreamMessage
      onMessage(message)
    } catch (e) {
      onError(new Error('Failed to parse message'))
    }
  }

  ws.onerror = () => {
    onError(new Error('WebSocket connection error'))
  }

  return ws
}

// Request builders for WebSocket
export interface LineExplainRequest {
  type: 'line'
  api_key: string
  model: string
  reasoning_effort?: string
  repo_id: string
  file_path: string
  line_number: number
  context_lines?: number
}

export interface RangeExplainRequest {
  type: 'range'
  api_key: string
  model: string
  reasoning_effort?: string
  repo_id: string
  file_path: string
  start_line: number
  end_line: number
}

export interface ArchitectureRequest {
  type: 'architecture'
  api_key: string
  model: string
  reasoning_effort?: string
  repo_id: string
}

export interface ArchitectureAgentRequest {
  type: 'architecture_agent'
  api_key: string
  model: string
  reasoning_effort?: string
  repo_id: string
  max_files_to_analyze?: number
}

export interface AgentStreamMessage extends StreamMessage {
  phase?: string
  status?: string
  detail?: string
  files_selected?: string[]
  has_context?: boolean
}

export async function getArchitectureStatus(repoId: string): Promise<{
  has_analysis: boolean
  timestamp?: string
  component_count?: number
  patterns?: string[]
}> {
  try {
    const response = await fetch(`${API_BASE}/explain/architecture-status/${repoId}`)
    if (!response.ok) return { has_analysis: false }
    return response.json()
  } catch {
    return { has_analysis: false }
  }
}

export interface ChatStreamRequest {
  api_key: string
  model: string
  reasoning_effort?: string
  repo_id: string
  file_path?: string
  line_range?: [number, number]
  message: string
  history: { role: 'user' | 'assistant'; content: string }[]
}

// Architecture content API (for loading cached analysis)
export interface ArchitectureContentResponse {
  has_analysis: boolean
  content: string
  component_count: number
  patterns: string[]
  timestamp?: string
}

export async function getArchitectureContent(repoId: string): Promise<ArchitectureContentResponse> {
  try {
    const response = await fetch(`${API_BASE}/explain/architecture-content/${repoId}`)
    if (!response.ok) return { has_analysis: false, content: '', component_count: 0, patterns: [] }
    return response.json()
  } catch {
    return { has_analysis: false, content: '', component_count: 0, patterns: [] }
  }
}

// File summary API
export interface FileSummaryRequest {
  type: 'file_summary'
  api_key: string
  model: string
  reasoning_effort?: string
  repo_id: string
  file_path: string
}

export async function getFileSummary(repoId: string, filePath: string): Promise<{ found: boolean; summary_md?: string }> {
  try {
    const params = new URLSearchParams({ file_path: filePath })
    const response = await fetch(`${API_BASE}/explain/file-summary/${repoId}?${params}`)
    if (!response.ok) return { found: false }
    return response.json()
  } catch {
    return { found: false }
  }
}
