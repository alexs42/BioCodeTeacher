import { describe, it, expect } from 'vitest'
import {
  DEFAULT_MODELS,
  getModelById,
  getDefaultModel,
  getApiModelId,
  validateCustomModel,
  ModelOption,
  ReasoningConfig,
  ProviderRouting,
} from './models'

describe('DEFAULT_MODELS', () => {
  it('should have exactly 7 models', () => {
    expect(DEFAULT_MODELS).toHaveLength(7)
  })

  it('should have Claude Opus 4.6 as the first and recommended model', () => {
    const opus = DEFAULT_MODELS[0]
    expect(opus.id).toBe('anthropic/claude-opus-4.6')
    expect(opus.name).toBe('Claude Opus 4.6')
    expect(opus.provider).toBe('Anthropic')
    expect(opus.recommended).toBe(true)
    expect(opus.contextWindow).toBe(1000000)
  })

  it('should have Claude Sonnet 4.6', () => {
    const sonnet = DEFAULT_MODELS.find(m => m.id === 'anthropic/claude-sonnet-4.6')
    expect(sonnet).toBeDefined()
    expect(sonnet!.provider).toBe('Anthropic')
    expect(sonnet!.contextWindow).toBe(200000)
  })

  it('should have GPT-5.4 with reasoning effort medium', () => {
    const gpt54 = DEFAULT_MODELS.find(m => m.id === 'openai/gpt-5.4')
    expect(gpt54).toBeDefined()
    expect(gpt54!.reasoning).toEqual({ effort: 'medium' })
    expect(gpt54!.contextWindow).toBe(1050000)
    expect(gpt54!.provider).toBe('OpenAI')
  })

  it('should have GPT-5.4 Azure ZDR with provider routing', () => {
    const azureGpt = DEFAULT_MODELS.find(m => m.id === 'openai/gpt-5.4--azure-zdr')
    expect(azureGpt).toBeDefined()
    expect(azureGpt!.apiModelId).toBe('openai/gpt-5.4')
    expect(azureGpt!.provider).toBe('OpenAI (Azure)')
    expect(azureGpt!.providerRouting).toEqual({ only: ['azure'], zdr: true, allow_fallbacks: false })
  })

  it('should have GLM-5 Turbo', () => {
    const glm = DEFAULT_MODELS.find(m => m.id === 'z-ai/glm-5-turbo')
    expect(glm).toBeDefined()
    expect(glm!.provider).toBe('Z.ai (Zhipu)')
    expect(glm!.contextWindow).toBe(128000)
  })

  it('should have Gemini 3.1 Pro with reasoning effort medium', () => {
    const geminiPro = DEFAULT_MODELS.find(m => m.id === 'google/gemini-3.1-pro-preview')
    expect(geminiPro).toBeDefined()
    expect(geminiPro!.provider).toBe('Google')
    expect(geminiPro!.contextWindow).toBe(1048576)
    expect(geminiPro!.reasoning).toEqual({ effort: 'medium' })
  })

  it('should have Gemini 3.0 Flash', () => {
    const geminiFlash = DEFAULT_MODELS.find(m => m.id === 'google/gemini-3-flash-preview')
    expect(geminiFlash).toBeDefined()
    expect(geminiFlash!.provider).toBe('Google')
    expect(geminiFlash!.contextWindow).toBe(1048576)
  })

  it('should only have one recommended model', () => {
    const recommended = DEFAULT_MODELS.filter(m => m.recommended)
    expect(recommended).toHaveLength(1)
  })

  it('all models should have valid provider/model-name ID format', () => {
    for (const model of DEFAULT_MODELS) {
      expect(model.id).toContain('/')
      expect(model.name.length).toBeGreaterThan(0)
      expect(model.provider.length).toBeGreaterThan(0)
      expect(model.contextWindow).toBeGreaterThan(0)
    }
  })
})

describe('getModelById', () => {
  it('should return model by ID', () => {
    const model = getModelById('anthropic/claude-opus-4.6')
    expect(model).toBeDefined()
    expect(model!.name).toBe('Claude Opus 4.6')
  })

  it('should return undefined for unknown model', () => {
    const model = getModelById('unknown/model')
    expect(model).toBeUndefined()
  })

  it('should search custom models when provided', () => {
    const custom: ModelOption[] = [{
      id: 'custom/model-1',
      name: 'Custom Model',
      provider: 'Custom',
      description: 'test',
      contextWindow: 50000,
    }]
    const model = getModelById('custom/model-1', custom)
    expect(model).toBeDefined()
    expect(model!.name).toBe('Custom Model')
  })

  it('should prefer default models over custom with same ID', () => {
    const custom: ModelOption[] = [{
      id: 'anthropic/claude-opus-4.6',
      name: 'Overridden Name',
      provider: 'Anthropic',
      description: 'test',
      contextWindow: 50000,
    }]
    const model = getModelById('anthropic/claude-opus-4.6', custom)
    expect(model).toBeDefined()
    // Should find the default one first since it's at the front of the spread array
    expect(model!.name).toBe('Claude Opus 4.6')
  })
})

describe('getDefaultModel', () => {
  it('should return the recommended model', () => {
    const model = getDefaultModel()
    expect(model.recommended).toBe(true)
    expect(model.id).toBe('anthropic/claude-opus-4.6')
  })
})

describe('validateCustomModel', () => {
  it('should return null for valid model', () => {
    const result = validateCustomModel({
      id: 'provider/model-name',
      name: 'Test Model',
      provider: 'Test Provider',
    })
    expect(result).toBeNull()
  })

  it('should require model ID', () => {
    const result = validateCustomModel({
      name: 'Test',
      provider: 'Test',
    })
    expect(result).toContain('ID')
  })

  it('should require model name', () => {
    const result = validateCustomModel({
      id: 'provider/model',
      provider: 'Test',
    })
    expect(result).toContain('name')
  })

  it('should require provider', () => {
    const result = validateCustomModel({
      id: 'provider/model',
      name: 'Test',
    })
    expect(result).toContain('Provider')
  })

  it('should require slash in model ID', () => {
    const result = validateCustomModel({
      id: 'noslash',
      name: 'Test',
      provider: 'Test',
    })
    expect(result).toContain('format')
  })

  it('should reject empty strings', () => {
    expect(validateCustomModel({ id: '', name: 'a', provider: 'a' })).not.toBeNull()
    expect(validateCustomModel({ id: 'a/b', name: '', provider: 'a' })).not.toBeNull()
    expect(validateCustomModel({ id: 'a/b', name: 'a', provider: '' })).not.toBeNull()
  })

  it('should reject whitespace-only strings', () => {
    expect(validateCustomModel({ id: '   ', name: 'a', provider: 'a' })).not.toBeNull()
    expect(validateCustomModel({ id: 'a/b', name: '  ', provider: 'a' })).not.toBeNull()
  })
})

describe('getApiModelId', () => {
  it('should return id when no apiModelId is set', () => {
    const model: ModelOption = {
      id: 'anthropic/claude-opus-4.6',
      name: 'Test',
      provider: 'Test',
      description: 'test',
      contextWindow: 100000,
    }
    expect(getApiModelId(model)).toBe('anthropic/claude-opus-4.6')
  })

  it('should return apiModelId when set', () => {
    const model: ModelOption = {
      id: 'openai/gpt-5.4--azure-zdr',
      apiModelId: 'openai/gpt-5.4',
      name: 'Test',
      provider: 'Test',
      description: 'test',
      contextWindow: 100000,
    }
    expect(getApiModelId(model)).toBe('openai/gpt-5.4')
  })

  it('should return correct API model ID for Azure ZDR model', () => {
    const azureModel = DEFAULT_MODELS.find(m => m.id === 'openai/gpt-5.4--azure-zdr')
    expect(azureModel).toBeDefined()
    expect(getApiModelId(azureModel!)).toBe('openai/gpt-5.4')
  })
})

describe('ReasoningConfig type', () => {
  it('should be assignable with valid effort values', () => {
    const configs: ReasoningConfig[] = [
      { effort: 'none' },
      { effort: 'minimal' },
      { effort: 'low' },
      { effort: 'medium' },
      { effort: 'high' },
      { effort: 'xhigh' },
    ]
    expect(configs).toHaveLength(6)
  })
})

describe('ProviderRouting type', () => {
  it('should be assignable with valid routing configs', () => {
    const configs: ProviderRouting[] = [
      { only: ['azure'], zdr: true, allow_fallbacks: false },
      { order: ['azure', 'openai'] },
      { data_collection: 'deny' },
      { ignore: ['openai'], zdr: true },
    ]
    expect(configs).toHaveLength(4)
  })
})
