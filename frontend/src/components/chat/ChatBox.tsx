import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, MessageSquare, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useCodeStore, ChatMessage } from '../../store/codeStore'
import { createChatStream, ChatStreamRequest } from '../../services/api'
import { getModelById } from '../../config/models'

interface QuickAction {
  label: string
  message: string
  requiresFile: boolean
  isArchitecture?: boolean
}

const QUICK_ACTIONS: QuickAction[] = [
  { label: 'Analyze architecture', message: '', requiresFile: false, isArchitecture: true },
  { label: 'Create diagram', message: 'Create a mermaid diagram showing the structure and relationships in this file.', requiresFile: true },
  { label: 'Explain with examples', message: 'Explain this code with concrete examples of how it works and when it would be called.', requiresFile: true },
  { label: 'Find potential bugs', message: 'Review this code for potential bugs, edge cases, or issues that could cause problems.', requiresFile: true },
  { label: 'Summarize file', message: 'Provide a concise summary of what this file does, its key exports, and its role in the project.', requiresFile: true },
]

export default function ChatBox() {
  const {
    apiKey,
    selectedModel,
    repoId,
    currentFile,
    selectedLine,
    selectedRange,
    chatMessages,
    addChatMessage,
    clearChat,
    setActiveView,
  } = useCodeStore()

  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [streamingResponse, setStreamingResponse] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current && isExpanded) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [chatMessages, streamingResponse, isExpanded])

  const handleSend = (overrideMessage?: string) => {
    const messageText = overrideMessage || input.trim()
    if (!messageText || !apiKey || !repoId || isLoading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: messageText,
    }

    addChatMessage(userMessage)
    if (!overrideMessage) setInput('')
    setIsLoading(true)
    setStreamingResponse('')
    setIsExpanded(true)

    // Close existing WebSocket
    if (wsRef.current) {
      wsRef.current.close()
    }

    let fullResponse = ''

    const ws = createChatStream(
      (msg) => {
        switch (msg.type) {
          case 'start':
            setStreamingResponse('')
            break
          case 'chunk':
            if (msg.content) {
              fullResponse += msg.content
              setStreamingResponse(fullResponse)
            }
            break
          case 'end':
            addChatMessage({
              role: 'assistant',
              content: fullResponse,
            })
            setStreamingResponse('')
            setIsLoading(false)
            break
          case 'error':
            addChatMessage({
              role: 'assistant',
              content: `Error: ${msg.content}`,
            })
            setStreamingResponse('')
            setIsLoading(false)
            break
        }
      },
      (error) => {
        addChatMessage({
          role: 'assistant',
          content: `Connection error: ${error.message}`,
        })
        setStreamingResponse('')
        setIsLoading(false)
      }
    )

    ws.onopen = () => {
      const modelConfig = getModelById(selectedModel)

      // Use selectedRange for line_range if available, otherwise fall back to +-5 around selectedLine
      let lineRange: [number, number] | undefined
      if (selectedRange) {
        lineRange = [selectedRange.start, selectedRange.end]
      } else if (selectedLine) {
        lineRange = [Math.max(1, selectedLine - 5), selectedLine + 5]
      }

      const request: ChatStreamRequest = {
        api_key: apiKey,
        model: selectedModel,
        reasoning_effort: modelConfig?.reasoning?.effort,
        repo_id: repoId,
        file_path: currentFile || undefined,
        line_range: lineRange,
        message: userMessage.content,
        history: chatMessages.slice(-10),
      }
      ws.send(JSON.stringify(request))
    }

    wsRef.current = ws
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const handleQuickAction = (action: QuickAction) => {
    if (!canUseActions) return
    if (action.isArchitecture) {
      // Trigger the architecture agent panel
      setActiveView('architecture')
      // The ArchitecturePanel will handle starting the analysis
      return
    }
    handleSend(action.message)
  }

  const hasMessages = chatMessages.length > 0 || streamingResponse

  // Filter quick actions by context
  const availableActions = QUICK_ACTIONS.filter((action) => {
    if (!repoId) return false
    if (action.requiresFile && !currentFile) return false
    return true
  })

  const canUseActions = !!apiKey && !isLoading

  return (
    <div className={`h-full flex flex-col bg-ct-surface ${!isExpanded ? 'overflow-hidden' : ''}`}>
      {/* Toggle header */}
      <div
        className="flex-shrink-0 flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-ct-bg/50 border-t border-ct-border"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-ct-primary" />
          <span className="text-sm font-medium">Chat</span>
          {chatMessages.length > 0 && (
            <span className="text-xs text-ct-text-secondary">
              ({chatMessages.length} messages)
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasMessages && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                clearChat()
              }}
              className="p-1 hover:bg-ct-bg rounded text-ct-text-secondary hover:text-ct-text"
              title="Clear chat"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <span className="text-xs text-ct-text-secondary">
            {isExpanded ? 'Collapse' : 'Expand'}
          </span>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <>
          {/* Messages */}
          <div className="flex-1 min-h-0 overflow-y-auto px-4 py-2 space-y-3 bg-ct-bg/50">
            {!hasMessages ? (
              <div className="h-full flex flex-col items-center justify-center text-ct-text-secondary text-sm gap-4">
                <p>Ask questions about the code you're viewing</p>
                {/* Quick action pills in empty state */}
                {availableActions.length > 0 && (
                  <div className="flex flex-wrap justify-center gap-2 max-w-xs">
                    {availableActions.map((action) => (
                      <button
                        key={action.label}
                        onClick={() => handleQuickAction(action)}
                        disabled={!canUseActions}
                        className="px-3 py-1.5 text-xs bg-ct-surface border border-ct-border rounded-full hover:border-ct-primary hover:text-ct-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <>
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                        msg.role === 'user'
                          ? 'bg-ct-primary text-white'
                          : 'bg-ct-surface border border-ct-border'
                      }`}
                    >
                      {msg.role === 'assistant' ? (
                        <div className="markdown-content prose-sm">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        msg.content
                      )}
                    </div>
                  </div>
                ))}

                {/* Streaming response */}
                {streamingResponse && (
                  <div className="flex justify-start">
                    <div className="max-w-[85%] rounded-lg px-3 py-2 text-sm bg-ct-surface border border-ct-border">
                      <div className="markdown-content prose-sm">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {streamingResponse}
                        </ReactMarkdown>
                      </div>
                      <span className="inline-block w-2 h-4 bg-ct-primary animate-pulse ml-1" />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Quick actions row (when messages exist) */}
          {hasMessages && availableActions.length > 0 && (
            <div className="flex-shrink-0 px-3 py-1.5 border-t border-ct-border overflow-x-auto">
              <div className="flex gap-1.5">
                {availableActions.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => handleQuickAction(action)}
                    disabled={!canUseActions}
                    className="flex-shrink-0 px-2.5 py-1 text-xs bg-ct-bg border border-ct-border rounded-full hover:border-ct-primary hover:text-ct-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="flex-shrink-0 p-3 border-t border-ct-border">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={apiKey ? 'Ask about this code...' : 'Enter API key first'}
                disabled={!apiKey || isLoading}
                className="flex-1 px-3 py-2 bg-ct-bg border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary disabled:opacity-50"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || !apiKey || isLoading}
                className="p-2 bg-ct-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
