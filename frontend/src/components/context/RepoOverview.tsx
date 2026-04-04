/**
 * Tier 1: Repository overview display.
 * Shows when repo is loaded but no file is selected.
 * Displays architecture analysis (streaming or cached), phase progress, and component list.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import { Brain, Loader2, RefreshCw, AlertTriangle, Search } from 'lucide-react'
import { useCodeStore } from '../../store/codeStore'
import { getArchitectureContent, getFileContent } from '../../services/api'
import { useArchitectureAnalysis } from '../../hooks/useArchitectureAnalysis'
import { PhaseTracker } from '../architecture/PhaseTracker'

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
        // Mermaid's own SVG output is safe — it sanitizes internally
        if (ref.current) ref.current.innerHTML = svg  // eslint-disable-line
      }).catch(() => {
        // Fallback: use textContent to prevent XSS from untrusted chart data
        if (ref.current) {
          ref.current.textContent = ''
          const pre = document.createElement('pre')
          pre.className = 'text-xs text-ct-text-secondary'
          pre.textContent = chart
          ref.current.appendChild(pre)
        }
      })
    } catch {
      if (ref.current) {
        ref.current.textContent = ''
        const pre = document.createElement('pre')
        pre.className = 'text-xs text-ct-text-secondary'
        pre.textContent = chart
        ref.current.appendChild(pre)
      }
    }
  }, [chart])
  return <div ref={ref} className="my-3 flex justify-center" />
}

export default function RepoOverview() {
  const {
    apiKey, repoId, repoPath,
    architectureAnalysis, architecturePhase, architecturePhaseDetail,
    isAnalyzingArchitecture, hasArchitectureContext, hasCachedAnalysis,
    autoAnalysisTriggered,
    setArchitectureAnalysis, setHasArchitectureContext,
    setAutoAnalysisTriggered, setCurrentFile,
  } = useCodeStore()

  const { startAnalysis } = useArchitectureAnalysis()
  const [completedPhases, setCompletedPhases] = useState<Set<string>>(new Set())
  const [isStale, setIsStale] = useState(false)

  const navigateToFile = useCallback(async (filePath: string) => {
    if (!repoId) return
    try {
      const data = await getFileContent(repoId, filePath)
      setCurrentFile(data.path, data.content, data.language)
    } catch { /* file might not exist */ }
  }, [repoId, setCurrentFile])

  // Auto-trigger: load cached analysis or start fresh
  useEffect(() => {
    if (!repoId || !apiKey || autoAnalysisTriggered) return
    setAutoAnalysisTriggered(true)

    if (hasCachedAnalysis) {
      getArchitectureContent(repoId).then((data) => {
        if (data.has_analysis && data.content) {
          setArchitectureAnalysis(data.content)
          setHasArchitectureContext(true)
        } else if (apiKey) {
          startAnalysis({ silent: true })
        }
      }).catch(() => {
        if (apiKey) startAnalysis({ silent: true })
      })
    } else {
      startAnalysis({ silent: true })
    }
  }, [repoId, apiKey, hasCachedAnalysis, autoAnalysisTriggered])

  // Track phase completion
  useEffect(() => {
    if (architecturePhaseDetail?.includes('complete') && architecturePhase) {
      setCompletedPhases(prev => new Set([...prev, architecturePhase]))
    }
  }, [architecturePhase, architecturePhaseDetail])

  // Check staleness
  useEffect(() => {
    if (!repoId || !hasArchitectureContext || isAnalyzingArchitecture) return
    fetch(`/api/explain/architecture-status/${repoId}`)
      .then(r => r.json())
      .then(data => setIsStale(data.is_stale === true))
      .catch(() => {})
  }, [repoId, hasArchitectureContext, isAnalyzingArchitecture])

  // Initialize mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false, theme: 'dark',
      themeVariables: {
        primaryColor: '#5b9cf5', primaryTextColor: '#e2e6f0', primaryBorderColor: '#252d3a',
        lineColor: '#5b9cf5', secondaryColor: '#12161e', tertiaryColor: '#0a0d12',
      },
    })
  }, [])

  const repoName = repoPath?.split(/[/\\]/).pop() || 'Repository'

  // No analysis yet and not analyzing
  if (!architectureAnalysis && !isAnalyzingArchitecture && !hasCachedAnalysis) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-6 text-center tier-enter">
        <div className="w-16 h-16 rounded-2xl bg-ct-surface-2 border border-ct-border flex items-center justify-center">
          <Search size={32} className="text-ct-warm" />
        </div>
        <div>
          <h3 className="text-xl font-display font-semibold text-ct-text mb-2">{repoName}</h3>
          <p className="text-sm text-ct-text-secondary max-w-md">
            {apiKey
              ? 'Ready to analyze this repository. Click below to start.'
              : 'Set up your API key in settings to enable architecture analysis.'}
          </p>
        </div>
        {apiKey && (
          <button onClick={() => startAnalysis({ silent: true })} disabled={!repoId}
            className="px-5 py-2.5 bg-ct-primary hover:bg-ct-primary/90 disabled:bg-ct-surface disabled:text-ct-text-secondary rounded-lg text-sm font-medium transition-colors">
            <span className="flex items-center gap-2"><Brain size={16} /> Analyze Architecture</span>
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-hidden tier-enter">
      {/* Phase tracker during analysis */}
      {isAnalyzingArchitecture && (
        <div className="border-b border-ct-border bg-ct-surface/50">
          <PhaseTracker
            phases={PHASES.map(p => ({ ...p, detail: p.id === architecturePhase ? architecturePhaseDetail : null }))}
            currentPhase={architecturePhase}
            completedPhases={completedPhases}
          />
          {architecturePhaseDetail && (
            <div className="px-4 pb-2 text-xs text-ct-text-secondary">{architecturePhaseDetail}</div>
          )}
        </div>
      )}

      {/* Analysis content */}
      <div className="flex-1 overflow-y-auto p-4 markdown-content ct-dotgrid">
        {architectureAnalysis ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children }) {
                const match = /language-(\w+)/.exec(className || '')
                const lang = match ? match[1] : ''
                const text = String(children).replace(/\n$/, '')
                if (lang === 'mermaid') return <MermaidDiagram chart={text} />
                if (!className && FILE_PATH_RE.test(text)) {
                  return (
                    <code className="bg-ct-surface px-1.5 py-0.5 rounded text-sm font-mono text-ct-primary cursor-pointer hover:underline"
                      onClick={() => navigateToFile(text)} title={`Open ${text}`}>{children}</code>
                  )
                }
                if (className) {
                  return <pre className="bg-ct-bg rounded-lg p-3 overflow-x-auto my-2"><code className={className}>{children}</code></pre>
                }
                return <code className="bg-ct-surface px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
              },
            }}
          >{architectureAnalysis}</ReactMarkdown>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-ct-text-secondary">
              <Loader2 className="w-8 h-8 text-ct-primary animate-spin mx-auto mb-3" />
              <p className="text-sm">Analyzing repository architecture...</p>
            </div>
          </div>
        )}
        {isAnalyzingArchitecture && architectureAnalysis && (
          <span className="inline-block w-2 h-4 bg-ct-warm animate-pulse ml-0.5" />
        )}
      </div>

      {/* Footer */}
      {!isAnalyzingArchitecture && architectureAnalysis && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-ct-border text-xs bg-ct-surface">
          <div className="flex items-center gap-3">
            {hasArchitectureContext && (
              <span className="text-ct-accent flex items-center gap-1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                Context active
              </span>
            )}
            {isStale && (
              <span className="text-ct-warm flex items-center gap-1"><AlertTriangle size={12} /> Files changed</span>
            )}
          </div>
          <button onClick={() => { startAnalysis(); setIsStale(false); setCompletedPhases(new Set()) }}
            className="flex items-center gap-1 text-ct-text-secondary hover:text-ct-text transition-colors">
            <RefreshCw size={12} /> Re-analyze
          </button>
        </div>
      )}
    </div>
  )
}
