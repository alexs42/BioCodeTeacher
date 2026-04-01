/**
 * Model configuration for OpenRouter integration.
 * Defines available AI models and their metadata.
 */

export interface ReasoningConfig {
  effort: "none" | "minimal" | "low" | "medium" | "high" | "xhigh"
}

export interface ProviderRouting {
  only?: string[]
  ignore?: string[]
  order?: string[]
  zdr?: boolean
  allow_fallbacks?: boolean
  data_collection?: "allow" | "deny"
}

export interface ModelOption {
  id: string
  /** Override model ID sent to OpenRouter (when id is a virtual/internal key) */
  apiModelId?: string
  name: string
  provider: string
  description: string
  contextWindow: number
  recommended?: boolean
  isCustom?: boolean
  reasoning?: ReasoningConfig
  providerRouting?: ProviderRouting
}

/** Get the model ID to send to OpenRouter (apiModelId if set, otherwise id). */
export function getApiModelId(model: ModelOption): string {
  return model.apiModelId || model.id
}

/**
 * Default models available in BioCodeTeacher.
 * These are pre-configured frontier models from OpenRouter.
 */
export const DEFAULT_MODELS: ModelOption[] = [
  {
    id: "anthropic/claude-opus-4.6",
    name: "Claude Opus 4.6",
    provider: "Anthropic",
    description: "Anthropic's strongest model for coding and long-running professional tasks, 1M context",
    contextWindow: 1000000,
    recommended: true
  },
  {
    id: "anthropic/claude-sonnet-4.6",
    name: "Claude Sonnet 4.6",
    provider: "Anthropic",
    description: "Fast, intelligent model balancing speed and capability, 200K context",
    contextWindow: 200000
  },
  {
    id: "openai/gpt-5.4",
    name: "GPT-5.4 (Thinking Medium)",
    provider: "OpenAI",
    description: "OpenAI's latest frontier model with multimodal reasoning, 1M context",
    contextWindow: 1050000,
    reasoning: { effort: "medium" }
  },
  {
    id: "openai/gpt-5.4--azure-zdr",
    apiModelId: "openai/gpt-5.4",
    name: "GPT-5.4 Azure ZDR",
    provider: "OpenAI (Azure)",
    description: "GPT-5.4 routed through Azure with zero data retention — your prompts are never stored or trained on",
    contextWindow: 1050000,
    reasoning: { effort: "medium" },
    providerRouting: { only: ["azure"], zdr: true, allow_fallbacks: false }
  },
  {
    id: "z-ai/glm-5-turbo",
    name: "GLM-5 Turbo",
    provider: "Z.ai (Zhipu)",
    description: "Zhipu's fast frontier model with strong multilingual and reasoning capabilities",
    contextWindow: 128000
  },
  {
    id: "google/gemini-3.1-pro-preview",
    name: "Gemini 3.1 Pro",
    provider: "Google",
    description: "Google's flagship frontier model with thinking support, 1M context",
    contextWindow: 1048576,
    reasoning: { effort: "medium" }
  },
  {
    id: "google/gemini-3-flash-preview",
    name: "Gemini 3.0 Flash",
    provider: "Google",
    description: "High-speed thinking model for agentic workflows and coding, 1M context",
    contextWindow: 1048576
  }
]

/**
 * Get a model by its ID.
 * Returns undefined if not found.
 */
export function getModelById(modelId: string, customModels: ModelOption[] = []): ModelOption | undefined {
  return [...DEFAULT_MODELS, ...customModels].find(m => m.id === modelId)
}

/**
 * Get the default model (recommended model or first in list).
 */
export function getDefaultModel(): ModelOption {
  return DEFAULT_MODELS.find(m => m.recommended) || DEFAULT_MODELS[0]
}

/**
 * Validate a custom model configuration.
 */
export function validateCustomModel(model: Partial<ModelOption>): string | null {
  if (!model.id || model.id.trim() === '') {
    return "Model ID is required"
  }
  if (!model.name || model.name.trim() === '') {
    return "Model name is required"
  }
  if (!model.provider || model.provider.trim() === '') {
    return "Provider is required"
  }
  if (!model.id.includes('/')) {
    return "Model ID should be in format 'provider/model-name'"
  }
  return null
}
