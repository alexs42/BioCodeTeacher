/**
 * Shared hook for triggering architecture analysis.
 * Used by both auto-analysis (on repo load) and manual re-analysis.
 */

import { useCallback, useRef } from 'react'
import { useCodeStore } from '../store/codeStore'
import { createExplanationStream, AgentStreamMessage } from '../services/api'
import { getModelById, getApiModelId } from '../config/models'

export function useArchitectureAnalysis() {
  const {
    apiKey, repoId, selectedModel,
    setArchitectureAnalysis, appendArchitectureAnalysis,
    setArchitecturePhase, setIsAnalyzingArchitecture,
    setHasArchitectureContext, setActiveView,
  } = useCodeStore()

  const wsRef = useRef<WebSocket | null>(null)
  const completedPhasesRef = useRef<Set<string>>(new Set())
  const selectedFilesRef = useRef<string[]>([])

  const startAnalysis = useCallback((opts?: { silent?: boolean }) => {
    if (!apiKey || !repoId) return

    // Reset state
    setArchitectureAnalysis(null)
    completedPhasesRef.current = new Set()
    selectedFilesRef.current = []
    setIsAnalyzingArchitecture(true)
    setHasArchitectureContext(false)
    if (!opts?.silent) {
      setActiveView('architecture')
    }

    const model = getModelById(selectedModel)
    const apiModel = model ? getApiModelId(model) : selectedModel
    const reasoning = model?.reasoning?.effort

    const ws = createExplanationStream(
      (msg: AgentStreamMessage) => {
        if (msg.type === 'phase') {
          const agentMsg = msg as AgentStreamMessage
          setArchitecturePhase(agentMsg.phase || null, agentMsg.detail)
          if (agentMsg.status === 'complete' && agentMsg.phase) {
            completedPhasesRef.current.add(agentMsg.phase)
          }
          if (agentMsg.files_selected) {
            selectedFilesRef.current = agentMsg.files_selected
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

  const cleanup = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close()
    }
  }, [])

  return { startAnalysis, cleanup }
}
