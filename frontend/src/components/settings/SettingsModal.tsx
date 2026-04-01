import { useState, useEffect } from 'react'
import { X, Key, Github, Eye, EyeOff, ExternalLink } from 'lucide-react'
import { useCodeStore, ApiProvider } from '../../store/codeStore'
import ModelSettings from './ModelSettings'

const PROVIDER_CONFIG: Record<ApiProvider, { label: string; placeholder: string; url: string; urlLabel: string }> = {
  openrouter: { label: 'OpenRouter', placeholder: 'sk-or-v1-...', url: 'https://openrouter.ai/keys', urlLabel: 'Manage keys at OpenRouter' },
  openai: { label: 'OpenAI', placeholder: 'sk-...', url: 'https://platform.openai.com/api-keys', urlLabel: 'Manage keys at OpenAI' },
  anthropic: { label: 'Anthropic', placeholder: 'sk-ant-...', url: 'https://console.anthropic.com/settings/keys', urlLabel: 'Manage keys at Anthropic' },
}

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { githubToken, selectedProvider, apiKeys, setSelectedProvider, setGithubToken } = useCodeStore()

  const [tempProvider, setTempProvider] = useState<ApiProvider>(selectedProvider)
  const [tempApiKey, setTempApiKey] = useState(apiKeys[selectedProvider] || '')
  const [tempGithubToken, setTempGithubToken] = useState(githubToken || '')
  const [showApiKey, setShowApiKey] = useState(false)
  const [showGithubToken, setShowGithubToken] = useState(false)
  const [saved, setSaved] = useState(false)

  // Sync when modal opens
  useEffect(() => {
    if (isOpen) {
      setTempProvider(selectedProvider)
      setTempApiKey(apiKeys[selectedProvider] || '')
      setTempGithubToken(githubToken || '')
    }
  }, [isOpen, selectedProvider, apiKeys, githubToken])

  if (!isOpen) return null

  const handleProviderChange = (provider: ApiProvider) => {
    setTempProvider(provider)
    setTempApiKey(apiKeys[provider] || '')
  }

  const handleSaveKeys = () => {
    setSelectedProvider(tempProvider)
    if (tempApiKey.trim()) {
      setTimeout(() => useCodeStore.getState().setApiKey(tempApiKey.trim()), 0)
    }
    if (tempGithubToken.trim()) {
      setGithubToken(tempGithubToken.trim())
    } else if (!tempGithubToken.trim() && githubToken) {
      setGithubToken('')
    }
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleClose = () => {
    setTempApiKey(apiKeys[selectedProvider] || '')
    setTempGithubToken(githubToken || '')
    setTempProvider(selectedProvider)
    setSaved(false)
    onClose()
  }

  const info = PROVIDER_CONFIG[tempProvider]

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-ct-surface border border-ct-border rounded-xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-ct-border">
          <h2 className="text-xl font-semibold">Settings</h2>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-ct-bg rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-ct-text-secondary" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          {/* API Keys Section */}
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-1">API Keys</h3>
              <p className="text-sm text-ct-text-secondary">
                Choose your API provider and manage credentials
              </p>
            </div>

            {/* Provider Selector */}
            <div className="grid grid-cols-3 gap-2">
              {(Object.entries(PROVIDER_CONFIG) as [ApiProvider, typeof PROVIDER_CONFIG['openrouter']][]).map(([key, { label }]) => (
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
                  {apiKeys[key] ? ' *' : ''}
                </button>
              ))}
            </div>

            {/* API Key for selected provider */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium">
                <Key className="w-4 h-4 text-ct-primary" />
                {info.label} API Key
              </label>
              <div className="relative">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={tempApiKey}
                  onChange={(e) => setTempApiKey(e.target.value)}
                  placeholder={info.placeholder}
                  className="w-full px-4 py-2.5 bg-ct-bg border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary pr-10"
                />
                <button
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ct-text-secondary hover:text-ct-text"
                >
                  {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <a
                href={info.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-ct-primary hover:underline"
              >
                {info.urlLabel}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {/* GitHub Token */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium">
                <Github className="w-4 h-4 text-ct-text-secondary" />
                GitHub Token
                <span className="text-ct-text-secondary text-xs">(optional)</span>
              </label>
              <div className="relative">
                <input
                  type={showGithubToken ? 'text' : 'password'}
                  value={tempGithubToken}
                  onChange={(e) => setTempGithubToken(e.target.value)}
                  placeholder="ghp_..."
                  className="w-full px-4 py-2.5 bg-ct-bg border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary pr-10"
                />
                <button
                  onClick={() => setShowGithubToken(!showGithubToken)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ct-text-secondary hover:text-ct-text"
                >
                  {showGithubToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Save Keys Button */}
            <button
              onClick={handleSaveKeys}
              disabled={!tempApiKey.trim()}
              className={`px-4 py-2 rounded-lg text-sm transition-all ${
                saved
                  ? 'bg-ct-accent/20 text-ct-accent border border-ct-accent/30'
                  : 'bg-ct-primary text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed'
              }`}
            >
              {saved ? 'Saved!' : 'Save Keys'}
            </button>
          </div>

          {/* Divider */}
          <div className="border-t border-ct-border" />

          {/* Model Settings */}
          <ModelSettings />
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-ct-border flex justify-end">
          <button
            onClick={handleClose}
            className="px-6 py-2 bg-ct-primary text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
