import { useRef, useCallback, useEffect } from 'react'
import Editor, { OnMount } from '@monaco-editor/react'
import { useCodeStore } from '../../store/codeStore'
import { createExplanationStream, LineExplainRequest, RangeExplainRequest } from '../../services/api'
import { getModelById } from '../../config/models'

// Monaco language mapping
const languageMap: Record<string, string> = {
  python: 'python',
  javascript: 'javascript',
  typescript: 'typescript',
  java: 'java',
  cpp: 'cpp',
  c: 'c',
  csharp: 'csharp',
  go: 'go',
  rust: 'rust',
  ruby: 'ruby',
  php: 'php',
  swift: 'swift',
  kotlin: 'kotlin',
  scala: 'scala',
  html: 'html',
  css: 'css',
  scss: 'scss',
  json: 'json',
  yaml: 'yaml',
  markdown: 'markdown',
  sql: 'sql',
  bash: 'shell',
  dockerfile: 'dockerfile',
  plaintext: 'plaintext',
}

type ExplainTarget =
  | { type: 'line'; line: number }
  | { type: 'range'; start: number; end: number }

export default function CodeEditor() {
  const {
    currentFile,
    fileContent,
    fileLanguage,
    selectedLine,
    selectedRange,
    isDarkMode,
    repoId,
    apiKey,
    selectedModel,
    setExplanation,
    setIsExplaining,
    appendExplanation,
  } = useCodeStore()

  const editorRef = useRef<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const decorationsRef = useRef<string[]>([])
  const requestExplanationRef = useRef<(target: ExplainTarget) => void>(() => {})

  // Request explanation for a line or range
  const requestExplanation = useCallback(
    (target: ExplainTarget) => {
      if (!apiKey || !repoId || !currentFile || !fileContent) {
        return
      }

      // Close existing WebSocket
      if (wsRef.current) {
        wsRef.current.close()
      }

      setIsExplaining(true)
      setExplanation(null)

      const ws = createExplanationStream(
        (msg) => {
          switch (msg.type) {
            case 'start':
              setExplanation('')
              break
            case 'chunk':
              if (msg.content) {
                appendExplanation(msg.content)
              }
              break
            case 'end':
              setIsExplaining(false)
              break
            case 'error':
              setExplanation(`Error: ${msg.content}`)
              setIsExplaining(false)
              break
          }
        },
        (error) => {
          setExplanation(`Connection error: ${error.message}`)
          setIsExplaining(false)
        }
      )

      ws.onopen = () => {
        const modelConfig = getModelById(selectedModel)
        if (target.type === 'line') {
          const request: LineExplainRequest = {
            type: 'line',
            api_key: apiKey,
            model: selectedModel,
            reasoning_effort: modelConfig?.reasoning?.effort,
            repo_id: repoId,
            file_path: currentFile,
            line_number: target.line,
            context_lines: 10,
          }
          ws.send(JSON.stringify(request))
        } else {
          const request: RangeExplainRequest = {
            type: 'range',
            api_key: apiKey,
            model: selectedModel,
            reasoning_effort: modelConfig?.reasoning?.effort,
            repo_id: repoId,
            file_path: currentFile,
            start_line: target.start,
            end_line: target.end,
          }
          ws.send(JSON.stringify(request))
        }
      }

      wsRef.current = ws
    },
    [apiKey, selectedModel, repoId, currentFile, fileContent, setIsExplaining, setExplanation, appendExplanation]
  )

  // Keep ref in sync so Monaco event handlers always call the latest version
  useEffect(() => {
    requestExplanationRef.current = requestExplanation
  }, [requestExplanation])

  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor

    // On mouseup, check if we have a multi-line selection or single click
    const domNode = editor.getDomNode()
    if (domNode) {
      domNode.addEventListener('mouseup', () => {
        const selection = editor.getSelection()
        if (!selection) return

        let startLine = selection.startLineNumber
        let endLine = selection.endLineNumber

        // If selection ends at column 1, the user didn't actually select that line
        if (endLine > startLine && selection.endColumn === 1) {
          endLine -= 1
        }

        if (endLine > startLine) {
          // Multi-line selection
          useCodeStore.getState().setSelectedRange({ start: startLine, end: endLine })
          requestExplanationRef.current({ type: 'range', start: startLine, end: endLine })
        } else {
          // Single line click
          const line = selection.startLineNumber
          useCodeStore.getState().setSelectedLine(line)
          requestExplanationRef.current({ type: 'line', line })
        }

      })
    }
  }

  // Update line/range highlighting when selection changes
  useEffect(() => {
    if (!editorRef.current) return

    const editor = editorRef.current
    const model = editor.getModel()
    if (!model) return

    // Clear previous decorations
    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [])

    if (selectedRange) {
      // Highlight the full range
      const newDecorations = []
      for (let line = selectedRange.start; line <= selectedRange.end; line++) {
        newDecorations.push({
          range: {
            startLineNumber: line,
            startColumn: 1,
            endLineNumber: line,
            endColumn: model.getLineMaxColumn(line),
          },
          options: {
            isWholeLine: true,
            className: 'selected-line-highlight',
            glyphMarginClassName: 'selected-line-glyph',
          },
        })
      }
      decorationsRef.current = editor.deltaDecorations([], newDecorations)
    } else if (selectedLine) {
      // Highlight single line
      const newDecorations = [
        {
          range: {
            startLineNumber: selectedLine,
            startColumn: 1,
            endLineNumber: selectedLine,
            endColumn: model.getLineMaxColumn(selectedLine),
          },
          options: {
            isWholeLine: true,
            className: 'selected-line-highlight',
            glyphMarginClassName: 'selected-line-glyph',
          },
        },
      ]
      decorationsRef.current = editor.deltaDecorations([], newDecorations)
    }
  }, [selectedLine, selectedRange])

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const monacoLanguage = languageMap[fileLanguage || ''] || 'plaintext'

  // Header label
  const selectionLabel = selectedRange
    ? `Lines ${selectedRange.start}-${selectedRange.end}`
    : selectedLine
      ? `Line ${selectedLine}`
      : null

  return (
    <div className="h-full flex flex-col">
      {/* File header */}
      <div className="h-10 flex items-center px-4 bg-ct-surface border-b border-ct-border">
        <span className="text-sm text-ct-text-secondary truncate">{currentFile}</span>
        {selectionLabel && (
          <span className="ml-auto text-xs text-ct-text-secondary">
            {selectionLabel}
          </span>
        )}
      </div>

      {/* Editor */}
      <div className="flex-1">
        <Editor
          height="100%"
          language={monacoLanguage}
          value={fileContent || ''}
          theme={isDarkMode ? 'vs-dark' : 'light'}
          onMount={handleEditorMount}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
            lineNumbers: 'on',
            renderLineHighlight: 'all',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            glyphMargin: true,
            folding: true,
            automaticLayout: true,
          }}
        />
      </div>

      {/* Line highlight styles */}
      <style>{`
        .selected-line-highlight {
          background-color: rgba(88, 166, 255, 0.15) !important;
        }
        .selected-line-glyph {
          background-color: var(--ct-primary);
          width: 3px !important;
          margin-left: 3px;
        }
      `}</style>
    </div>
  )
}
