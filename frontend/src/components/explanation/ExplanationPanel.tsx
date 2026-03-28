import { useEffect, useRef, useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import { Allotment } from 'allotment'
import { Loader2, Sparkles, ArrowUp, ArrowDown, Brain, GitBranch, Microscope } from 'lucide-react'
import { useCodeStore } from '../../store/codeStore'
import { getFileContext, FileContextResponse, createExplanationStream } from '../../services/api'
import { getModelById } from '../../config/models'
import ChatBox from '../chat/ChatBox'
import { ArchitecturePanel } from '../architecture/ArchitecturePanel'

// Initialize mermaid with dark theme
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#58a6ff',
    primaryTextColor: '#e6edf3',
    primaryBorderColor: '#30363d',
    lineColor: '#8b949e',
    secondaryColor: '#161b22',
    tertiaryColor: '#0d1117',
  },
})

// Custom component to render Mermaid diagrams
function MermaidDiagram({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current || !chart) return

    const id = `mermaid-${Date.now()}`

    mermaid
      .render(id, chart)
      .then(({ svg }) => {
        if (ref.current) {
          ref.current.innerHTML = svg
        }
      })
      .catch(() => {
        // Clean up any leaked error elements mermaid may have injected
        document.querySelectorAll(`#${id}, #d${id}`).forEach(el => el.remove())
        // Fall back to showing raw code
        if (ref.current) {
          ref.current.innerHTML = `<pre class="bg-ct-bg p-4 rounded-lg overflow-x-auto text-sm font-mono text-ct-text-secondary"><code>${chart.replace(/</g, '&lt;')}</code></pre>`
        }
      })
  }, [chart])

  return <div ref={ref} className="my-4 flex justify-center overflow-x-auto" />
}

export default function ExplanationPanel() {
  const {
    selectedLine,
    selectedRange,
    fileContent,
    currentFile,
    explanation,
    isExplaining,
    setSelectedLine,
    repoId,
    activeView,
    setActiveView,
    architectureAnalysis,
    isAnalyzingArchitecture,
    hasArchitectureContext,
  } = useCodeStore()

  const contentRef = useRef<HTMLDivElement>(null)
  const [fileCtx, setFileCtx] = useState<FileContextResponse | null>(null)

  const [isAnalyzingFile, setIsAnalyzingFile] = useState(false)

  // Fetch file-specific architecture context when file changes
  useEffect(() => {
    if (!repoId || !currentFile || !hasArchitectureContext) {
      setFileCtx(null)
      return
    }
    getFileContext(repoId, currentFile).then(setFileCtx).catch(() => setFileCtx(null))
  }, [repoId, currentFile, hasArchitectureContext])

  const { apiKey, selectedModel } = useCodeStore()

  const handleDeepAnalyze = useCallback(() => {
    if (!apiKey || !repoId || !currentFile) return
    setIsAnalyzingFile(true)
    const model = getModelById(selectedModel)
    const ws = createExplanationStream(
      (msg) => {
        if (msg.type === 'file_analyzed' || msg.type === 'error') {
          setIsAnalyzingFile(false)
          ws.close()
          // Refresh file context after analysis
          if (msg.type === 'file_analyzed' && repoId && currentFile) {
            getFileContext(repoId, currentFile).then(setFileCtx).catch(() => {})
          }
        }
      },
      () => setIsAnalyzingFile(false)
    )
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'analyze_file',
        api_key: apiKey,
        model: selectedModel,
        reasoning_effort: model?.reasoning?.effort,
        repo_id: repoId,
        file_path: currentFile,
      }))
    }
  }, [apiKey, repoId, currentFile, selectedModel])

  // Get the selected line(s) content
  const lines = fileContent?.split('\n') || []
  const isRange = !!selectedRange
  const hasSelection = !!selectedLine || !!selectedRange

  const selectedCodeContent = selectedRange
    ? lines.slice(selectedRange.start - 1, selectedRange.end).join('\n')
    : selectedLine
      ? lines[selectedLine - 1] ?? null
      : null

  const headerLabel = selectedRange
    ? `Lines ${selectedRange.start}-${selectedRange.end}`
    : selectedLine
      ? `Line ${selectedLine}`
      : null

  // Navigate to previous/next line (only in single-line mode)
  const goToPrevLine = () => {
    if (selectedLine && selectedLine > 1) {
      setSelectedLine(selectedLine - 1)
    }
  }

  const goToNextLine = () => {
    if (selectedLine && selectedLine < lines.length) {
      setSelectedLine(selectedLine + 1)
    }
  }

  // Scroll to top when explanation changes
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = 0
    }
  }, [selectedLine, selectedRange])

  // Custom markdown components
  const components = {
    code: ({ className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '')
      const language = match ? match[1] : ''

      // Render mermaid diagrams
      if (language === 'mermaid') {
        return <MermaidDiagram chart={String(children).trim()} />
      }

      // Inline code
      if (!className) {
        return (
          <code className="bg-ct-surface px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
            {children}
          </code>
        )
      }

      // Code block
      return (
        <pre className="bg-ct-bg p-4 rounded-lg overflow-x-auto my-4">
          <code className={`text-sm font-mono ${className}`} {...props}>
            {children}
          </code>
        </pre>
      )
    },
    table: ({ children }: any) => (
      <div className="overflow-x-auto my-4">
        <table className="w-full border-collapse">{children}</table>
      </div>
    ),
    th: ({ children }: any) => (
      <th className="border border-ct-border bg-ct-surface px-3 py-2 text-left text-sm font-medium">
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td className="border border-ct-border px-3 py-2 text-sm">{children}</td>
    ),
    h2: ({ children }: any) => (
      <h2 className="text-lg font-semibold text-ct-primary border-b border-ct-border pb-2 mt-6 mb-3 first:mt-0">
        {children}
      </h2>
    ),
    h3: ({ children }: any) => (
      <h3 className="text-base font-medium text-ct-text mt-4 mb-2">{children}</h3>
    ),
    p: ({ children }: any) => <p className="text-sm leading-relaxed my-2">{children}</p>,
    ul: ({ children }: any) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
    li: ({ children }: any) => <li className="text-sm">{children}</li>,
  }

  const showArchTab = !!repoId && (!!architectureAnalysis || isAnalyzingArchitecture)

  return (
    <div className="h-full flex flex-col bg-ct-bg">
      {/* View tabs — only show when architecture analysis exists */}
      {showArchTab && (
        <div className="flex-shrink-0 flex border-b border-ct-border text-xs">
          <button
            onClick={() => setActiveView('explanation')}
            className={`px-4 py-2 transition-colors ${
              activeView === 'explanation'
                ? 'text-ct-primary border-b-2 border-ct-primary'
                : 'text-ct-text-secondary hover:text-ct-text'
            }`}
          >
            Explanation
          </button>
          <button
            onClick={() => setActiveView('architecture')}
            className={`px-4 py-2 transition-colors flex items-center gap-1.5 ${
              activeView === 'architecture'
                ? 'text-ct-primary border-b-2 border-ct-primary'
                : 'text-ct-text-secondary hover:text-ct-text'
            }`}
          >
            <Brain size={12} />
            Architecture
            {hasArchitectureContext && (
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" title="Context active" />
            )}
          </button>
        </div>
      )}

      {/* Architecture view */}
      {activeView === 'architecture' && showArchTab ? (
        <div className="flex-1 min-h-0">
          <Allotment vertical>
            <Allotment.Pane minSize={100} preferredSize="70%">
              <ArchitecturePanel />
            </Allotment.Pane>
            <Allotment.Pane minSize={48} preferredSize={200}>
              <ChatBox />
            </Allotment.Pane>
          </Allotment>
        </div>
      ) : (
      <>
      {/* Header with line navigation — stays outside Allotment */}
      {currentFile && hasSelection && (
        <div className="flex-shrink-0 px-4 py-3 bg-ct-surface border-b border-ct-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-ct-text-secondary uppercase tracking-wider">
              {headerLabel}
            </span>
            {/* Show prev/next only for single-line mode */}
            {!isRange && (
              <div className="flex items-center gap-1">
                <button
                  onClick={goToPrevLine}
                  disabled={!selectedLine || selectedLine <= 1}
                  className="p-1 hover:bg-ct-bg rounded disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Previous line"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
                <button
                  onClick={goToNextLine}
                  disabled={!selectedLine || selectedLine >= lines.length}
                  className="p-1 hover:bg-ct-bg rounded disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Next line"
                >
                  <ArrowDown className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {/* Selected code display */}
          <div className="bg-ct-bg rounded-lg p-3 border border-ct-border max-h-32 overflow-auto">
            <code className="text-base font-mono text-ct-primary whitespace-pre-wrap break-all">
              {selectedCodeContent?.trim() || '(empty line)'}
            </code>
          </div>

          {/* Connections indicator */}
          {fileCtx?.found && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
              <GitBranch className="w-3 h-3 text-ct-accent flex-shrink-0" />
              <span className="text-ct-text-secondary truncate max-w-[200px]" title={fileCtx.role}>
                {fileCtx.role}
              </span>
              {fileCtx.imports && fileCtx.imports.length > 0 && (
                <>
                  <span className="text-ct-text-secondary">|</span>
                  <span className="text-ct-text-secondary">
                    imports {fileCtx.imports.map(i => i.path.split('/').pop()).join(', ')}
                  </span>
                </>
              )}
              {fileCtx.imported_by && fileCtx.imported_by.length > 0 && (
                <>
                  <span className="text-ct-text-secondary">|</span>
                  <span className="text-ct-text-secondary">
                    used by {fileCtx.imported_by.map(i => i.path.split('/').pop()).join(', ')}
                  </span>
                </>
              )}
            </div>
          )}

          {/* Deep analyze button — file not in index */}
          {hasArchitectureContext && fileCtx && !fileCtx.found && (
            <div className="mt-2">
              <button
                onClick={handleDeepAnalyze}
                disabled={isAnalyzingFile}
                className="flex items-center gap-1.5 text-xs text-ct-text-secondary hover:text-ct-primary transition-colors disabled:opacity-50"
              >
                {isAnalyzingFile ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Microscope className="w-3 h-3" />
                )}
                {isAnalyzingFile ? 'Analyzing...' : 'Deep analyze this file'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Resizable explanation + chat split */}
      <div className="flex-1 min-h-0">
        <Allotment vertical>
          <Allotment.Pane minSize={100} preferredSize="70%">
            {/* Explanation content */}
            <div ref={contentRef} className="h-full overflow-auto p-4">
              {!currentFile ? (
                <div className="h-full flex items-center justify-center text-ct-text-secondary">
                  <div className="text-center space-y-3">
                    <Sparkles className="w-12 h-12 mx-auto text-ct-primary opacity-50" />
                    <p className="text-sm">Open a file and click on a line to see an explanation</p>
                  </div>
                </div>
              ) : !hasSelection ? (
                <div className="h-full flex items-center justify-center text-ct-text-secondary">
                  <div className="text-center space-y-3">
                    <Sparkles className="w-12 h-12 mx-auto text-ct-primary opacity-50" />
                    <p className="text-sm">Click on any line in the editor to get an explanation</p>
                  </div>
                </div>
              ) : isExplaining && !explanation ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 text-ct-primary animate-spin" />
                </div>
              ) : explanation ? (
                <div className="markdown-content">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={components}
                  >
                    {explanation}
                  </ReactMarkdown>
                  {isExplaining && (
                    <span className="inline-block w-2 h-4 bg-ct-primary animate-pulse ml-1" />
                  )}
                </div>
              ) : (
                <div className="text-ct-text-secondary text-sm">
                  Waiting for explanation...
                </div>
              )}
            </div>
          </Allotment.Pane>

          <Allotment.Pane minSize={48} preferredSize={200}>
            <ChatBox />
          </Allotment.Pane>
        </Allotment>
      </div>
      </>
      )}
    </div>
  )
}
