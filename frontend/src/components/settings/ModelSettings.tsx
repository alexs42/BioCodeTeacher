import { useState } from 'react'
import { Check, Plus, Trash2, Sparkles } from 'lucide-react'
import { useCodeStore, ModelOption } from '../../store/codeStore'
import { DEFAULT_MODELS, validateCustomModel } from '../../config/models'

export default function ModelSettings() {
  const { selectedModel, customModels, setSelectedModel, addCustomModel, removeCustomModel } = useCodeStore()
  const [showAddForm, setShowAddForm] = useState(false)
  const [newModel, setNewModel] = useState<Partial<ModelOption>>({
    id: '',
    name: '',
    provider: '',
    description: '',
    contextWindow: 100000
  })
  const [error, setError] = useState<string | null>(null)

  const allModels = [...DEFAULT_MODELS, ...customModels]

  const handleAddModel = () => {
    const validationError = validateCustomModel(newModel)
    if (validationError) {
      setError(validationError)
      return
    }

    // Check for duplicate ID
    if (allModels.some(m => m.id === newModel.id)) {
      setError('A model with this ID already exists')
      return
    }

    addCustomModel(newModel as ModelOption)
    setNewModel({
      id: '',
      name: '',
      provider: '',
      description: '',
      contextWindow: 100000
    })
    setShowAddForm(false)
    setError(null)
  }

  const handleRemoveModel = (modelId: string) => {
    if (selectedModel === modelId) {
      // Switch to default model if removing the selected one
      setSelectedModel(DEFAULT_MODELS[0].id)
    }
    removeCustomModel(modelId)
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-1">AI Model Selection</h3>
        <p className="text-sm text-ct-text-secondary">
          Choose which model to use for code explanations and chat
        </p>
      </div>

      {/* Model Grid */}
      <div className="grid gap-3">
        {allModels.map(model => (
          <div
            key={model.id}
            onClick={() => setSelectedModel(model.id)}
            className={`p-4 border rounded-lg cursor-pointer transition-all ${
              selectedModel === model.id
                ? 'border-ct-primary bg-ct-primary/5'
                : 'border-ct-border hover:border-ct-primary/50'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium flex items-center gap-2">
                    {model.name}
                    {model.recommended && (
                      <span className="text-xs px-2 py-0.5 bg-ct-primary/20 text-ct-primary rounded-full">
                        Recommended
                      </span>
                    )}
                  </h4>
                </div>
                <p className="text-xs text-ct-text-secondary mb-2">
                  {model.provider} • {model.contextWindow?.toLocaleString()} tokens
                </p>
                <p className="text-sm text-ct-text-secondary">
                  {model.description}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {selectedModel === model.id && (
                  <div className="flex items-center justify-center w-5 h-5 bg-ct-primary rounded-full">
                    <Check className="w-3 h-3 text-white" />
                  </div>
                )}
                {model.isCustom && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemoveModel(model.id)
                    }}
                    className="p-1 hover:bg-red-500/10 rounded transition-colors"
                    title="Remove custom model"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Custom Model */}
      <div className="border-t border-ct-border pt-6">
        {!showAddForm ? (
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-ct-bg border border-ct-border rounded-lg hover:border-ct-primary transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Custom Model
          </button>
        ) : (
          <div className="space-y-4 p-4 bg-ct-bg border border-ct-border rounded-lg">
            <div className="flex items-center justify-between">
              <h4 className="font-medium flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-ct-primary" />
                Add Custom Model
              </h4>
              <button
                onClick={() => {
                  setShowAddForm(false)
                  setError(null)
                }}
                className="text-sm text-ct-text-secondary hover:text-ct-text"
              >
                Cancel
              </button>
            </div>

            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
                {error}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Model ID <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={newModel.id || ''}
                  onChange={(e) => setNewModel({ ...newModel, id: e.target.value })}
                  placeholder="e.g., anthropic/claude-3-opus"
                  className="w-full px-3 py-2 bg-ct-surface border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary"
                />
                <p className="text-xs text-ct-text-secondary mt-1">
                  OpenRouter model ID (provider/model-name)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Display Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={newModel.name || ''}
                  onChange={(e) => setNewModel({ ...newModel, name: e.target.value })}
                  placeholder="e.g., Claude 3 Opus"
                  className="w-full px-3 py-2 bg-ct-surface border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Provider <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={newModel.provider || ''}
                  onChange={(e) => setNewModel({ ...newModel, provider: e.target.value })}
                  placeholder="e.g., Anthropic"
                  className="w-full px-3 py-2 bg-ct-surface border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Description
                </label>
                <textarea
                  value={newModel.description || ''}
                  onChange={(e) => setNewModel({ ...newModel, description: e.target.value })}
                  placeholder="Brief description of the model"
                  rows={2}
                  className="w-full px-3 py-2 bg-ct-surface border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Context Window (tokens)
                </label>
                <input
                  type="number"
                  value={newModel.contextWindow || 100000}
                  onChange={(e) => setNewModel({ ...newModel, contextWindow: parseInt(e.target.value) || 100000 })}
                  className="w-full px-3 py-2 bg-ct-surface border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary"
                />
              </div>
            </div>

            <button
              onClick={handleAddModel}
              className="w-full px-4 py-2 bg-ct-primary text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              Add Model
            </button>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="p-4 bg-ct-bg border border-ct-border rounded-lg text-sm text-ct-text-secondary">
        <p className="font-medium text-ct-text mb-2">About Model Selection</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Different models have different strengths and costs</li>
          <li>Claude Opus 4.6 is recommended for complex code analysis</li>
          <li>You can add any model available on OpenRouter</li>
          <li>Find model IDs at <a href="https://openrouter.ai/models" target="_blank" rel="noopener noreferrer" className="text-ct-primary hover:underline">openrouter.ai/models</a></li>
        </ul>
      </div>
    </div>
  )
}
