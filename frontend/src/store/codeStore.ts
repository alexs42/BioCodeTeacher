import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { ModelOption, DEFAULT_MODELS, getDefaultModel } from '../config/models'

// Types
export interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  language?: string
  children?: FileNode[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface SelectedRange {
  start: number
  end: number
}

export type { ModelOption }

interface CodeStore {
  // API Configuration
  apiKey: string | null
  githubToken: string | null
  setApiKey: (key: string) => void
  setGithubToken: (token: string) => void

  // Model Selection
  selectedModel: string
  customModels: ModelOption[]
  setSelectedModel: (modelId: string) => void
  addCustomModel: (model: ModelOption) => void
  removeCustomModel: (modelId: string) => void
  getAllModels: () => ModelOption[]

  // Repository state
  repoId: string | null
  repoPath: string | null
  fileTree: FileNode | null
  setRepo: (id: string, path: string, tree: FileNode) => void
  clearRepo: () => void

  // File state
  currentFile: string | null
  fileContent: string | null
  fileLanguage: string | null
  setCurrentFile: (path: string, content: string, language: string) => void
  clearFile: () => void

  // Line selection
  selectedLine: number | null
  selectedRange: SelectedRange | null
  setSelectedLine: (line: number | null) => void
  setSelectedRange: (range: SelectedRange | null) => void

  // Explanation state
  explanation: string | null
  isExplaining: boolean
  setExplanation: (text: string | null) => void
  setIsExplaining: (loading: boolean) => void
  appendExplanation: (chunk: string) => void

  // Chat state
  chatMessages: ChatMessage[]
  addChatMessage: (message: ChatMessage) => void
  clearChat: () => void

  // Architecture analysis state
  architectureAnalysis: string | null
  architecturePhase: string | null
  architecturePhaseDetail: string | null
  isAnalyzingArchitecture: boolean
  hasArchitectureContext: boolean
  activeView: 'explanation' | 'architecture'
  setArchitectureAnalysis: (text: string | null) => void
  appendArchitectureAnalysis: (chunk: string) => void
  setArchitecturePhase: (phase: string | null, detail?: string) => void
  setIsAnalyzingArchitecture: (loading: boolean) => void
  setHasArchitectureContext: (has: boolean) => void
  setActiveView: (view: 'explanation' | 'architecture') => void

  // File summary state (tier 2)
  fileSummary: string | null
  isGeneratingFileSummary: boolean
  setFileSummary: (text: string | null) => void
  appendFileSummary: (chunk: string) => void
  setIsGeneratingFileSummary: (loading: boolean) => void

  // Auto-analysis
  autoAnalysisTriggered: boolean
  setAutoAnalysisTriggered: (triggered: boolean) => void
  hasCachedAnalysis: boolean
  setHasCachedAnalysis: (has: boolean) => void

  // UI state
  isDarkMode: boolean
  toggleDarkMode: () => void
  showSetupModal: boolean
  setShowSetupModal: (show: boolean) => void
  showSettingsModal: boolean
  setShowSettingsModal: (show: boolean) => void
}

export const useCodeStore = create<CodeStore>()(
  persist(
    (set) => ({
      // API Configuration
      apiKey: null,
      githubToken: null,
      setApiKey: (key) => set({ apiKey: key, showSetupModal: false }),
      setGithubToken: (token) => set({ githubToken: token }),

      // Model Selection
      selectedModel: getDefaultModel().id,
      customModels: [],
      setSelectedModel: (modelId) => set({ selectedModel: modelId }),
      addCustomModel: (model) => set((state) => ({
        customModels: [...state.customModels, { ...model, isCustom: true }]
      })),
      removeCustomModel: (modelId) => set((state) => ({
        customModels: state.customModels.filter(m => m.id !== modelId)
      })),
      getAllModels: (): ModelOption[] => {
        // Access state through useCodeStore.getState() after initialization
        if (typeof useCodeStore !== 'undefined' && useCodeStore.getState) {
          const state = useCodeStore.getState()
          return [...DEFAULT_MODELS, ...state.customModels]
        }
        return DEFAULT_MODELS
      },

      // Repository state
      repoId: null,
      repoPath: null,
      fileTree: null,
      setRepo: (id, path, tree) => set({
        repoId: id,
        repoPath: path,
        fileTree: tree,
        currentFile: null,
        fileContent: null,
        selectedLine: null,
        selectedRange: null,
        explanation: null,
        fileSummary: null,
        isGeneratingFileSummary: false,
        autoAnalysisTriggered: false,
      }),
      clearRepo: () => set({
        repoId: null,
        repoPath: null,
        fileTree: null,
        currentFile: null,
        fileContent: null,
        selectedLine: null,
        selectedRange: null,
        explanation: null,
        architectureAnalysis: null,
        architecturePhase: null,
        architecturePhaseDetail: null,
        isAnalyzingArchitecture: false,
        hasArchitectureContext: false,
        activeView: 'explanation',
        fileSummary: null,
        isGeneratingFileSummary: false,
        autoAnalysisTriggered: false,
        hasCachedAnalysis: false,
      }),

      // File state
      currentFile: null,
      fileContent: null,
      fileLanguage: null,
      setCurrentFile: (path, content, language) => set({
        currentFile: path,
        fileContent: content,
        fileLanguage: language,
        selectedLine: null,
        selectedRange: null,
        explanation: null,
        fileSummary: null,
        isGeneratingFileSummary: false,
      }),
      clearFile: () => set({
        currentFile: null,
        fileContent: null,
        fileLanguage: null,
        selectedLine: null,
        selectedRange: null,
        explanation: null,
      }),

      // Line selection
      selectedLine: null,
      selectedRange: null,
      setSelectedLine: (line) => set({ selectedLine: line, selectedRange: null }),
      setSelectedRange: (range) => set({
        selectedRange: range,
        selectedLine: range ? range.start : null,
      }),

      // Explanation state
      explanation: null,
      isExplaining: false,
      setExplanation: (text) => set({ explanation: text }),
      setIsExplaining: (loading) => set({ isExplaining: loading }),
      appendExplanation: (chunk) => set((state) => ({
        explanation: (state.explanation || '') + chunk,
      })),

      // Chat state
      chatMessages: [],
      addChatMessage: (message) => set((state) => ({
        chatMessages: [...state.chatMessages, message],
      })),
      clearChat: () => set({ chatMessages: [] }),

      // Architecture analysis state
      architectureAnalysis: null,
      architecturePhase: null,
      architecturePhaseDetail: null,
      isAnalyzingArchitecture: false,
      hasArchitectureContext: false,
      activeView: 'explanation',
      setArchitectureAnalysis: (text) => set({ architectureAnalysis: text }),
      appendArchitectureAnalysis: (chunk) => set((state) => ({
        architectureAnalysis: (state.architectureAnalysis || '') + chunk,
      })),
      setArchitecturePhase: (phase, detail) => set({
        architecturePhase: phase,
        architecturePhaseDetail: detail || null,
      }),
      setIsAnalyzingArchitecture: (loading) => set({ isAnalyzingArchitecture: loading }),
      setHasArchitectureContext: (has) => set({ hasArchitectureContext: has }),
      setActiveView: (view) => set({ activeView: view }),

      // File summary state
      fileSummary: null,
      isGeneratingFileSummary: false,
      setFileSummary: (text) => set({ fileSummary: text }),
      appendFileSummary: (chunk) => set((state) => ({
        fileSummary: (state.fileSummary || '') + chunk,
      })),
      setIsGeneratingFileSummary: (loading) => set({ isGeneratingFileSummary: loading }),

      // Auto-analysis
      autoAnalysisTriggered: false,
      setAutoAnalysisTriggered: (triggered) => set({ autoAnalysisTriggered: triggered }),
      hasCachedAnalysis: false,
      setHasCachedAnalysis: (has) => set({ hasCachedAnalysis: has }),

      // UI state
      isDarkMode: true,
      toggleDarkMode: () => set((state) => ({ isDarkMode: !state.isDarkMode })),
      showSetupModal: true,
      setShowSetupModal: (show) => set({ showSetupModal: show }),
      showSettingsModal: false,
      setShowSettingsModal: (show) => set({ showSettingsModal: show }),
    }),
    {
      name: 'codeteacher-storage',
      version: 2,
      partialize: (state) => ({
        apiKey: state.apiKey,
        githubToken: state.githubToken,
        isDarkMode: state.isDarkMode,
        selectedModel: state.selectedModel,
        customModels: state.customModels,
        showSetupModal: state.showSetupModal,
      }),
      migrate: (persisted: any, version: number) => {
        if (version < 2) {
          // v0/v1 → v2: model IDs changed (gpt-5.2/5.3-codex → gpt-5.4, gemini-3-pro → gemini-3.1-pro)
          // Reset to default if stored model no longer exists
          const knownIds = DEFAULT_MODELS.map(m => m.id)
          if (persisted.selectedModel && !knownIds.includes(persisted.selectedModel)) {
            persisted.selectedModel = getDefaultModel().id
          }
        }
        return persisted
      },
    }
  )
)
