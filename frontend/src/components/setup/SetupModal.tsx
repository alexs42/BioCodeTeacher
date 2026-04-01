import { useState } from 'react'
import { X, Key, Github, ExternalLink, Eye, EyeOff, Sparkles } from 'lucide-react'
import { useCodeStore, ApiProvider } from '../../store/codeStore'
import { getModelById, getModelsForProvider } from '../../config/models'

const PROVIDER_INFO: Record<ApiProvider, { label: string; keyPrefix: string; keyUrl: string; keyLabel: string }> = {
  openrouter: { label: 'OpenRouter', keyPrefix: 'sk-or-v1-...', keyUrl: 'https://openrouter.ai/keys', keyLabel: 'Get your API key from OpenRouter' },
  openai: { label: 'OpenAI', keyPrefix: 'sk-...', keyUrl: 'https://platform.openai.com/api-keys', keyLabel: 'Get your API key from OpenAI' },
  anthropic: { label: 'Anthropic', keyPrefix: 'sk-ant-...', keyUrl: 'https://console.anthropic.com/settings/keys', keyLabel: 'Get your API key from Anthropic' },
}

export default function SetupModal() {
  const {
    apiKey,
    githubToken,
    selectedModel,
    selectedProvider,
    apiKeys,
    customModels,
    setSelectedProvider,
    setGithubToken,
    setSelectedModel,
    setShowSetupModal
  } = useCodeStore()

  const [tempProvider, setTempProvider] = useState<ApiProvider>(selectedProvider)
  const [tempApiKey, setTempApiKey] = useState(apiKeys[selectedProvider] || '')
  const [tempGithubToken, setTempGithubToken] = useState(githubToken || '')
  const [tempModel, setTempModel] = useState(selectedModel)
  const [showApiKeyField, setShowApiKeyField] = useState(false)
  const [showGithubToken, setShowGithubToken] = useState(false)

  const providerModels = getModelsForProvider(tempProvider, customModels)
  const currentModel = getModelById(tempModel, customModels)

  const handleProviderChange = (provider: ApiProvider) => {
    setTempProvider(provider)
    setTempApiKey(apiKeys[provider] || '')
    // Switch to first model for the new provider if current model doesn't match
    const available = getModelsForProvider(provider, customModels)
    const currentStillValid = available.some(m => m.id === tempModel)
    if (!currentStillValid && available.length > 0) {
      setTempModel(available[0].id)
    }
  }

  const handleSave = () => {
    if (tempApiKey.trim()) {
      setSelectedProvider(tempProvider)
      // Small delay to ensure provider is set before key
      setTimeout(() => {
        useCodeStore.getState().setApiKey(tempApiKey.trim())
      }, 0)
    }
    if (tempGithubToken.trim()) {
      setGithubToken(tempGithubToken.trim())
    }
    setSelectedModel(tempModel)
    if (tempApiKey.trim()) {
      setShowSetupModal(false)
    }
  }

  const canClose = !!apiKey
  const info = PROVIDER_INFO[tempProvider]

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-ct-surface border border-ct-border rounded-xl max-w-lg w-full shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-ct-border">
          <h2 className="text-xl font-semibold">Welcome to <span className="text-ct-primary">Bio</span>CodeTeacher</h2>
          {canClose && (
            <button
              onClick={() => setShowSetupModal(false)}
              className="p-1 hover:bg-ct-bg rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-ct-text-secondary" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Introduction */}
          <p className="text-ct-text-secondary">
            BioCodeTeacher helps you understand bioinformatics code — single-cell analysis, spatial transcriptomics, digital pathology.
            Choose your API provider and enter your key to get started.
          </p>

          {/* Provider Selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium">API Provider</label>
            <div className="grid grid-cols-3 gap-2">
              {(Object.entries(PROVIDER_INFO) as [ApiProvider, typeof PROVIDER_INFO['openrouter']][]).map(([key, { label }]) => (
                <button
                  key={key}
                  onClick={() => handleProviderChange(key)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
                    tempProvider === key
                      ? 'bg-ct-primary/10 border-ct-primary text-ct-primary'
                      : 'bg-ct-bg border-ct-border text-ct-text-secondary hover:border-ct-text-secondary'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* API Key */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium">
              <Key className="w-4 h-4 text-ct-primary" />
              {info.label} API Key
              <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <input
                type={showApiKeyField ? 'text' : 'password'}
                value={tempApiKey}
                onChange={(e) => setTempApiKey(e.target.value)}
                placeholder={info.keyPrefix}
                className="w-full px-4 py-3 bg-ct-bg border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary pr-10"
              />
              <button
                onClick={() => setShowApiKeyField(!showApiKeyField)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-ct-text-secondary hover:text-ct-text"
              >
                {showApiKeyField ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <a
              href={info.keyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-ct-primary hover:underline"
            >
              {info.keyLabel}
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium">
              <Sparkles className="w-4 h-4 text-ct-primary" />
              AI Model
            </label>
            <select
              value={tempModel}
              onChange={(e) => setTempModel(e.target.value)}
              className="w-full px-4 py-3 bg-ct-bg border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary"
            >
              {providerModels.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name} {model.recommended ? '* Recommended' : ''} {model.provider ? `(${model.provider})` : ''}
                </option>
              ))}
            </select>
            {currentModel && (
              <p className="text-xs text-ct-text-secondary">
                {currentModel.description}
              </p>
            )}
          </div>

          {/* GitHub Token (optional) */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium">
              <Github className="w-4 h-4 text-ct-text-secondary" />
              GitHub Token
              <span className="text-ct-text-secondary text-xs">(optional, for private repos)</span>
            </label>
            <div className="relative">
              <input
                type={showGithubToken ? 'text' : 'password'}
                value={tempGithubToken}
                onChange={(e) => setTempGithubToken(e.target.value)}
                placeholder="ghp_..."
                className="w-full px-4 py-3 bg-ct-bg border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary pr-10"
              />
              <button
                onClick={() => setShowGithubToken(!showGithubToken)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-ct-text-secondary hover:text-ct-text"
              >
                {showGithubToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Info box */}
          <div className="bg-ct-bg border border-ct-border rounded-lg p-4 text-sm text-ct-text-secondary">
            <p className="font-medium text-ct-text mb-2">How it works:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Open a bioinformatics project (Scanpy, Seurat, Snakemake, etc.)</li>
              <li>Browse and select an analysis script or notebook</li>
              <li>Click on any line — get biological reasoning, data state changes, parameter guidance</li>
              <li>Use the chat to ask follow-up questions about the biology</li>
            </ol>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-ct-border flex justify-end gap-3">
          {canClose && (
            <button
              onClick={() => setShowSetupModal(false)}
              className="px-4 py-2 text-ct-text-secondary hover:text-ct-text transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={!tempApiKey.trim()}
            className="px-6 py-2 bg-ct-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            {apiKey ? 'Save Changes' : 'Get Started'}
          </button>
        </div>
      </div>
    </div>
  )
}
