import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { RefreshCw, Brain, AlertTriangle } from 'lucide-react'
import { useCodeStore } from '../../store/codeStore'
import { createExplanationStream, AgentStreamMessage, getFileContent } from '../../services/api'
import { getModelById, getApiModelId } from '../../config/models'
import { PhaseTracker } from './PhaseTracker'
import mermaid from 'mermaid'

const FILE_PATH_RE = /^[\w./\\-]+\.\w{1,6}$/

const PHASES = [
  { id: 'structure_scan', label: 'Structure' },
  { id: 'key_file_identification', label: 'File Selection' },
  { id: 'deep_analysis', label: 'Analysis' },
  { id: 'synthesis', label: 'Synthesis' },
]

function MermaidDiagram({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current || !chart.trim()) return
    const id = `mermaid-arch-${Math.random().toString(36).slice(2)}`
    try {
      mermaid.render(id, chart).then(({ svg }) => {
        if (ref.current) ref.current.innerHTML = svg
      }).catch(() => {
        if (ref.current) ref.current.textContent = chart
      })
    } catch {
      if (ref.current) ref.current.textContent = chart
    }
  }, [chart])

  return <div ref={ref} className="my-3 flex justify-center" />
}

export function ArchitecturePanel() {
  const {
    apiKey, repoId, selectedModel, architectureAnalysis,
    architecturePhase, architecturePhaseDetail,
    isAnalyzingArchitecture, hasArchitectureContext,
    setArchitectureAnalysis, appendArchitectureAnalysis,
    setArchitecturePhase, setIsAnalyzingArchitecture,
    setHasArchitectureContext, setActiveView, setCurrentFile,
  } = useCodeStore()

  const navigateToFile = useCallback(async (filePath: string) => {
    if (!repoId) return
    try {
      const data = await getFileContent(repoId, filePath)
      setCurrentFile(data.path, data.content, data.language)
      setActiveView('explanation')
    } catch {
      // File might not exist or path might be partial — ignore silently
    }
  }, [repoId, setCurrentFile, setActiveView])

  const [completedPhases, setCompletedPhases] = useState<Set<string>>(new Set())
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [isStale, setIsStale] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  // Check staleness when architecture is loaded and not analyzing
  useEffect(() => {
    if (!repoId || !hasArchitectureContext || isAnalyzingArchitecture) return
    fetch(`/api/explain/architecture-status/${repoId}`)
      .then(r => r.json())
      .then(data => setIsStale(data.is_stale === true))
      .catch(() => {})
  }, [repoId, hasArchitectureContext, isAnalyzingArchitecture])

  const startAnalysis = useCallback(() => {
    if (!apiKey || !repoId) return

    // Reset state
    setArchitectureAnalysis(null)
    setCompletedPhases(new Set())
    setSelectedFiles([])
    setIsAnalyzingArchitecture(true)
    setHasArchitectureContext(false)
    setActiveView('architecture')

    const model = getModelById(selectedModel)
    const apiModel = model ? getApiModelId(model) : selectedModel
    const reasoning = model?.reasoning?.effort

    const ws = createExplanationStream(
      (msg: AgentStreamMessage) => {
        if (msg.type === 'phase') {
          const agentMsg = msg as AgentStreamMessage
          setArchitecturePhase(agentMsg.phase || null, agentMsg.detail)
          if (agentMsg.status === 'complete' && agentMsg.phase) {
            setCompletedPhases(prev => new Set([...prev, agentMsg.phase!]))
          }
          if (agentMsg.files_selected) {
            setSelectedFiles(agentMsg.files_selected)
          }
        } else if (msg.type === 'chunk' && msg.content) {
          appendArchitectureAnalysis(msg.content)
        } else if (msg.type === 'end') {
          setIsAnalyzingArchitecture(false)
          setArchitecturePhase(null)
          if ((msg as AgentStreamMessage).has_context) {
            setHasArchitectureContext(true)
          }
        } else if (msg.type === 'error') {
          setIsAnalyzingArchitecture(false)
          setArchitecturePhase(null, msg.content || 'Analysis failed')
        }
      },
      (error) => {
        setIsAnalyzingArchitecture(false)
        setArchitecturePhase(null, error.message)
      }
    )

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'architecture_agent',
        api_key: apiKey,
        model: apiModel,
        reasoning_effort: reasoning,
        provider_routing: model?.providerRouting,
        repo_id: repoId,
      }))
    }

    wsRef.current = ws
  }, [apiKey, repoId, selectedModel, setArchitectureAnalysis, appendArchitectureAnalysis,
      setArchitecturePhase, setIsAnalyzingArchitecture, setHasArchitectureContext, setActiveView])

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, [])

  // Initialize mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#58a6ff',
        primaryTextColor: '#e6edf3',
        primaryBorderColor: '#30363d',
        lineColor: '#58a6ff',
        secondaryColor: '#161b22',
        tertiaryColor: '#0d1117',
      },
    })
  }, [])

  // No analysis yet — show start button
  if (!architectureAnalysis && !isAnalyzingArchitecture) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-6 text-center">
        <Brain size={48} className="text-ct-text-secondary" />
        <div>
          <h3 className="text-lg font-medium text-ct-text mb-1">Architecture Analysis</h3>
          <p className="text-sm text-ct-text-secondary max-w-md">
            Agentically examines your repository to understand its architecture,
            component relationships, and design patterns.
          </p>
        </div>
        <button
          onClick={startAnalysis}
          disabled={!apiKey || !repoId}
          className="px-4 py-2 bg-ct-primary hover:bg-ct-primary/90 disabled:bg-ct-surface disabled:text-ct-text-secondary
                     rounded-lg text-sm font-medium transition-colors"
        >
          Analyze Architecture
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Phase tracker */}
      {isAnalyzingArchitecture && (
        <div className="border-b border-ct-border bg-ct-surface/50">
          <PhaseTracker
            phases={PHASES.map(p => ({
              ...p,
              detail: p.id === architecturePhase ? architecturePhaseDetail : null,
            }))}
            currentPhase={architecturePhase}
            completedPhases={completedPhases}
          />
          {architecturePhaseDetail && (
            <div className="px-3 pb-2 text-xs text-ct-text-secondary">{architecturePhaseDetail}</div>
          )}
          {selectedFiles.length > 0 && architecturePhase !== 'synthesis' && (
            <div className="px-3 pb-2 text-xs text-ct-text-secondary">
              Files: {selectedFiles.slice(0, 5).join(', ')}
              {selectedFiles.length > 5 && ` +${selectedFiles.length - 5} more`}
            </div>
          )}
        </div>
      )}

      {/* Analysis content */}
      <div className="flex-1 overflow-y-auto p-4 markdown-content">
        {architectureAnalysis ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children }) {
                const match = /language-(\w+)/.exec(className || '')
                const lang = match ? match[1] : ''
                const text = String(children).replace(/\n$/, '')

                if (lang === 'mermaid') {
                  return <MermaidDiagram chart={text} />
                }

                // Inline code that looks like a file path — make clickable
                if (!className && FILE_PATH_RE.test(text)) {
                  return (
                    <code
                      className="bg-ct-surface px-1.5 py-0.5 rounded text-sm font-mono text-ct-primary cursor-pointer hover:underline"
                      onClick={() => navigateToFile(text)}
                      title={`Open ${text}`}
                    >
                      {children}
                    </code>
                  )
                }

                // Code block
                if (className) {
                  return (
                    <pre className="bg-ct-bg rounded-lg p-3 overflow-x-auto my-2">
                      <code className={className}>{children}</code>
                    </pre>
                  )
                }

                // Regular inline code
                return (
                  <code className="bg-ct-surface px-1.5 py-0.5 rounded text-sm font-mono">
                    {children}
                  </code>
                )
              },
            }}
          >
            {architectureAnalysis}
          </ReactMarkdown>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-ct-text-secondary">
              <div className="animate-pulse">Analyzing repository...</div>
            </div>
          </div>
        )}

        {/* Streaming cursor */}
        {isAnalyzingArchitecture && architectureAnalysis && (
          <span className="inline-block w-2 h-4 bg-ct-primary animate-pulse ml-0.5" />
        )}
      </div>

      {/* Footer with context badge, staleness, and re-analyze */}
      {!isAnalyzingArchitecture && architectureAnalysis && (
        <div className="flex items-center justify-between px-3 py-2 border-t border-ct-border text-xs">
          <div className="flex items-center gap-3">
            {hasArchitectureContext && (
              <span className="text-ct-accent flex items-center gap-1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                Context active
              </span>
            )}
            {isStale && (
              <span className="text-ct-warm flex items-center gap-1">
                <AlertTriangle size={12} />
                Files changed — re-analyze recommended
              </span>
            )}
          </div>
          <button
            onClick={() => { startAnalysis(); setIsStale(false) }}
            className="flex items-center gap-1 text-ct-text-secondary hover:text-ct-text transition-colors ml-auto"
          >
            <RefreshCw size={12} /> Re-analyze
          </button>
        </div>
      )}
    </div>
  )
}
