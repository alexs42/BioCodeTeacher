/**
 * Tier 2: File summary display.
 * Shows when a file is selected but no line is clicked.
 * Streams an educational file summary with connections and key components.
 */

import { useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Loader2, FileText, ArrowRight } from 'lucide-react'
import { useCodeStore } from '../../store/codeStore'
import {
  getFileSummary, getFileContext, FileContextResponse,
  createExplanationStream, getFileContent,
} from '../../services/api'
import { getModelById, getApiModelId } from '../../config/models'
import { useState } from 'react'

export default function FileSummary() {
  const {
    repoId, currentFile, fileLanguage, apiKey, selectedModel,
    fileSummary, isGeneratingFileSummary,
    hasArchitectureContext,
    setFileSummary, appendFileSummary, setIsGeneratingFileSummary,
    setCurrentFile,
  } = useCodeStore()

  const [fileCtx, setFileCtx] = useState<FileContextResponse | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // Fetch file context (connections) from architecture
  useEffect(() => {
    if (!repoId || !currentFile || !hasArchitectureContext) {
      setFileCtx(null)
      return
    }
    getFileContext(repoId, currentFile).then(setFileCtx).catch(() => setFileCtx(null))
  }, [repoId, currentFile, hasArchitectureContext])

  // Fetch or generate file summary
  useEffect(() => {
    if (!repoId || !currentFile || !apiKey) return
    if (fileSummary || isGeneratingFileSummary) return

    // Try cached summary first
    getFileSummary(repoId, currentFile).then((data) => {
      if (data.found && data.summary_md) {
        setFileSummary(data.summary_md)
      } else {
        // Generate via streaming
        generateFileSummary()
      }
    }).catch(() => {
      generateFileSummary()
    })
  }, [repoId, currentFile, apiKey])

  const generateFileSummary = useCallback(() => {
    if (!apiKey || !repoId || !currentFile) return
    setIsGeneratingFileSummary(true)
    setFileSummary(null)

    const model = getModelById(selectedModel)
    const apiModel = model ? getApiModelId(model) : selectedModel
    const ws = createExplanationStream(
      (msg) => {
        if (msg.type === 'chunk' && msg.content) {
          appendFileSummary(msg.content)
        } else if (msg.type === 'end') {
          setIsGeneratingFileSummary(false)
          ws.close()
        } else if (msg.type === 'error') {
          setIsGeneratingFileSummary(false)
          ws.close()
        }
      },
      () => setIsGeneratingFileSummary(false)
    )

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'file_summary',
        api_key: apiKey,
        model: apiModel,
        reasoning_effort: model?.reasoning?.effort,
        provider_routing: model?.providerRouting,
        repo_id: repoId,
        file_path: currentFile,
      }))
    }

    wsRef.current = ws
  }, [apiKey, repoId, currentFile, selectedModel])

  useEffect(() => {
    return () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.close()
    }
  }, [])

  const navigateToFile = useCallback(async (filePath: string) => {
    if (!repoId) return
    try {
      const data = await getFileContent(repoId, filePath)
      setCurrentFile(data.path, data.content, data.language)
    } catch { /* ignore */ }
  }, [repoId, setCurrentFile])

  const fileName = currentFile?.split(/[/\\]/).pop() || 'File'

  return (
    <div className="h-full flex flex-col tier-enter">
      {/* File header */}
      <div className="flex-shrink-0 px-4 py-3 bg-ct-surface border-b border-ct-border">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-ct-warm" />
          <span className="text-sm font-display font-semibold text-ct-text">{fileName}</span>
          {fileLanguage && (
            <span className="text-xs px-2 py-0.5 bg-ct-surface-2 border border-ct-border rounded-full text-ct-text-secondary">
              {fileLanguage}
            </span>
          )}
        </div>

        {/* Connections */}
        {fileCtx?.found && (
          <div className="mt-2 space-y-1">
            {fileCtx.role && (
              <p className="text-xs text-ct-text-secondary">{fileCtx.role}</p>
            )}
            <div className="flex flex-wrap gap-1.5">
              {fileCtx.imports?.map((imp) => (
                <button key={imp.path}
                  onClick={() => navigateToFile(imp.path)}
                  className="flex items-center gap-1 text-xs px-2 py-1 bg-ct-bg border border-ct-border rounded-md hover:border-ct-primary hover:text-ct-primary transition-colors">
                  <ArrowRight className="w-3 h-3" />
                  {imp.path.split('/').pop()}
                </button>
              ))}
              {fileCtx.imported_by?.map((imp) => (
                <button key={imp.path}
                  onClick={() => navigateToFile(imp.path)}
                  className="flex items-center gap-1 text-xs px-2 py-1 bg-ct-bg border border-ct-border rounded-md hover:border-ct-accent hover:text-ct-accent transition-colors">
                  <ArrowRight className="w-3 h-3 rotate-180" />
                  {imp.path.split('/').pop()}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Summary content */}
      <div className="flex-1 overflow-auto p-4">
        {!fileSummary && isGeneratingFileSummary ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-ct-primary animate-spin mx-auto mb-3" />
              <p className="text-sm text-ct-text-secondary">Generating file summary...</p>
            </div>
          </div>
        ) : fileSummary ? (
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}
              components={{
                h2: ({ children }: any) => <h2 className="text-lg font-semibold text-ct-primary border-b border-ct-border pb-2 mt-6 mb-3 first:mt-0">{children}</h2>,
                h3: ({ children }: any) => <h3 className="text-base font-medium text-ct-text mt-4 mb-2">{children}</h3>,
                p: ({ children }: any) => <p className="text-sm leading-relaxed my-2">{children}</p>,
                ul: ({ children }: any) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
                ol: ({ children }: any) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
                li: ({ children }: any) => <li className="text-sm">{children}</li>,
                code: ({ className, children, ...props }: any) => {
                  if (!className) return <code className="bg-ct-surface px-1.5 py-0.5 rounded text-sm font-mono" {...props}>{children}</code>
                  return <pre className="bg-ct-bg p-4 rounded-lg overflow-x-auto my-4"><code className={`text-sm font-mono ${className}`} {...props}>{children}</code></pre>
                },
              }}
            >{fileSummary}</ReactMarkdown>
            {isGeneratingFileSummary && <span className="inline-block w-2 h-4 bg-ct-warm animate-pulse ml-1" />}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-ct-text-secondary">
            <p className="text-sm">Click on a line to get an explanation, or wait for the file summary to load.</p>
          </div>
        )}
      </div>
    </div>
  )
}
