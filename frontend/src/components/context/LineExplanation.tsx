/**
 * Tier 3: Line/range explanation display.
 * Extracted from the original ExplanationPanel line explanation logic.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import { Loader2, ArrowUp, ArrowDown, GitBranch, Microscope } from 'lucide-react'
import { useCodeStore } from '../../store/codeStore'
import { getFileContext, FileContextResponse, createExplanationStream } from '../../services/api'
import { getModelById, getApiModelId } from '../../config/models'

function MermaidDiagram({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current || !chart) return
    const id = `mermaid-${Date.now()}`
    mermaid.render(id, chart).then(({ svg }) => {
      if (ref.current) ref.current.innerHTML = svg
    }).catch(() => {
      document.querySelectorAll(`#${id}, #d${id}`).forEach(el => el.remove())
      if (ref.current) {
        ref.current.innerHTML = `<pre class="bg-ct-bg p-4 rounded-lg overflow-x-auto text-sm font-mono text-ct-text-secondary"><code>${chart.replace(/</g, '&lt;')}</code></pre>`
      }
    })
  }, [chart])
  return <div ref={ref} className="my-4 flex justify-center overflow-x-auto" />
}

export default function LineExplanation() {
  const {
    selectedLine, selectedRange, fileContent, currentFile,
    explanation, isExplaining, setSelectedLine,
    repoId, hasArchitectureContext, apiKey, selectedModel,
  } = useCodeStore()

  const contentRef = useRef<HTMLDivElement>(null)
  const [fileCtx, setFileCtx] = useState<FileContextResponse | null>(null)
  const [isAnalyzingFile, setIsAnalyzingFile] = useState(false)

  useEffect(() => {
    if (!repoId || !currentFile || !hasArchitectureContext) {
      setFileCtx(null)
      return
    }
    getFileContext(repoId, currentFile).then(setFileCtx).catch(() => setFileCtx(null))
  }, [repoId, currentFile, hasArchitectureContext])

  const handleDeepAnalyze = useCallback(() => {
    if (!apiKey || !repoId || !currentFile) return
    setIsAnalyzingFile(true)
    const model = getModelById(selectedModel)
    const apiModel = model ? getApiModelId(model) : selectedModel
    const ws = createExplanationStream(
      (msg) => {
        if (msg.type === 'file_analyzed' || msg.type === 'error') {
          setIsAnalyzingFile(false)
          ws.close()
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
        model: apiModel,
        reasoning_effort: model?.reasoning?.effort,
        provider_routing: model?.providerRouting,
        repo_id: repoId,
        file_path: currentFile,
      }))
    }
  }, [apiKey, repoId, currentFile, selectedModel])

  const lines = fileContent?.split('\n') || []
  const isRange = !!selectedRange
  const selectedCodeContent = selectedRange
    ? lines.slice(selectedRange.start - 1, selectedRange.end).join('\n')
    : selectedLine ? lines[selectedLine - 1] ?? null : null

  const headerLabel = selectedRange
    ? `Lines ${selectedRange.start}-${selectedRange.end}`
    : selectedLine ? `Line ${selectedLine}` : null

  const goToPrevLine = () => { if (selectedLine && selectedLine > 1) setSelectedLine(selectedLine - 1) }
  const goToNextLine = () => { if (selectedLine && selectedLine < lines.length) setSelectedLine(selectedLine + 1) }

  useEffect(() => {
    if (contentRef.current) contentRef.current.scrollTop = 0
  }, [selectedLine, selectedRange])

  const components = {
    code: ({ className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '')
      const language = match ? match[1] : ''
      if (language === 'mermaid') return <MermaidDiagram chart={String(children).trim()} />
      if (!className) {
        return <code className="bg-ct-surface px-1.5 py-0.5 rounded text-sm font-mono" {...props}>{children}</code>
      }
      return (
        <pre className="bg-ct-bg p-4 rounded-lg overflow-x-auto my-4">
          <code className={`text-sm font-mono ${className}`} {...props}>{children}</code>
        </pre>
      )
    },
    h2: ({ children }: any) => <h2 className="text-lg font-semibold text-ct-primary border-b border-ct-border pb-2 mt-6 mb-3 first:mt-0">{children}</h2>,
    h3: ({ children }: any) => <h3 className="text-base font-medium text-ct-text mt-4 mb-2">{children}</h3>,
    p: ({ children }: any) => <p className="text-sm leading-relaxed my-2">{children}</p>,
    ul: ({ children }: any) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
    li: ({ children }: any) => <li className="text-sm">{children}</li>,
  }

  return (
    <div className="h-full flex flex-col tier-enter">
      {/* Header with line navigation */}
      <div className="flex-shrink-0 px-4 py-3 bg-ct-surface border-b border-ct-border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-ct-text-secondary uppercase tracking-wider font-display">
            {headerLabel}
          </span>
          {!isRange && (
            <div className="flex items-center gap-1">
              <button onClick={goToPrevLine} disabled={!selectedLine || selectedLine <= 1}
                className="p-1 hover:bg-ct-bg rounded disabled:opacity-30 disabled:cursor-not-allowed" title="Previous line">
                <ArrowUp className="w-4 h-4" />
              </button>
              <button onClick={goToNextLine} disabled={!selectedLine || selectedLine >= lines.length}
                className="p-1 hover:bg-ct-bg rounded disabled:opacity-30 disabled:cursor-not-allowed" title="Next line">
                <ArrowDown className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
        <div className="bg-ct-bg rounded-lg p-3 border border-ct-border max-h-32 overflow-auto">
          <code className="text-base font-mono text-ct-primary whitespace-pre-wrap break-all">
            {selectedCodeContent?.trim() || '(empty line)'}
          </code>
        </div>

        {fileCtx?.found && (
          <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
            <GitBranch className="w-3 h-3 text-ct-accent flex-shrink-0" />
            <span className="text-ct-text-secondary truncate max-w-[200px]" title={fileCtx.role}>{fileCtx.role}</span>
            {fileCtx.imports && fileCtx.imports.length > 0 && (
              <><span className="text-ct-text-secondary">|</span><span className="text-ct-text-secondary">imports {fileCtx.imports.map(i => i.path.split('/').pop()).join(', ')}</span></>
            )}
            {fileCtx.imported_by && fileCtx.imported_by.length > 0 && (
              <><span className="text-ct-text-secondary">|</span><span className="text-ct-text-secondary">used by {fileCtx.imported_by.map(i => i.path.split('/').pop()).join(', ')}</span></>
            )}
          </div>
        )}

        {hasArchitectureContext && fileCtx && !fileCtx.found && (
          <div className="mt-2">
            <button onClick={handleDeepAnalyze} disabled={isAnalyzingFile}
              className="flex items-center gap-1.5 text-xs text-ct-text-secondary hover:text-ct-primary transition-colors disabled:opacity-50">
              {isAnalyzingFile ? <Loader2 className="w-3 h-3 animate-spin" /> : <Microscope className="w-3 h-3" />}
              {isAnalyzingFile ? 'Analyzing...' : 'Deep analyze this file'}
            </button>
          </div>
        )}
      </div>

      {/* Explanation content */}
      <div ref={contentRef} className="flex-1 overflow-auto p-4">
        {isExplaining && !explanation ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-ct-primary animate-spin" />
          </div>
        ) : explanation ? (
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
              {explanation}
            </ReactMarkdown>
            {isExplaining && <span className="inline-block w-2 h-4 bg-ct-warm animate-pulse ml-1" />}
          </div>
        ) : (
          <div className="text-ct-text-secondary text-sm">Waiting for explanation...</div>
        )}
      </div>
    </div>
  )
}
