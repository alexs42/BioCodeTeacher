# OpenRouter Model Selection Implementation Plan

## Executive Summary

This plan outlines the implementation of user-configurable model selection for the OpenRouter API integration in CodeTeacher. Currently, the model is hardcoded to `anthropic/claude-opus-4-5-20251101`. This enhancement will allow users to select from popular models (Opus 4.5, GPT-5.2 Pro, Gemini 3.0 Pro, etc.) and customize the list as models are updated.

## Current State Analysis

### Backend (`backend/services/openrouter.py`)
- **Line 12**: `MODEL_ID = "anthropic/claude-opus-4-5-20251101"` - Hardcoded constant
- The model ID is used in both `stream_completion()` and `complete()` methods
- No mechanism for dynamic model selection exists

### Frontend
- **SetupModal** (`frontend/src/components/setup/SetupModal.tsx`): Only configures API keys
- **Store** (`frontend/src/store/codeStore.ts`): Uses Zustand with persistence, stores API keys but no model preference
- No UI for model selection

### Request Flow
1. Frontend components send `api_key` in requests
2. Backend creates `OpenRouterService(api_key)` instance
3. Service uses hardcoded `MODEL_ID` in API calls

## Implementation Strategy

### Option A: Frontend-Driven Model Selection (RECOMMENDED)
**Pros:**
- User has immediate control without backend changes
- Model preference persists in browser storage
- Easy to update model list without backend deployment
- Backend remains stateless and simple

**Cons:**
- Model ID sent with every request (minimal overhead)
- Model validation happens at OpenRouter API (not locally)

### Option B: Backend Configuration
**Pros:**
- Centralized model management
- Could validate models server-side

**Cons:**
- Requires backend deployment to update models
- Less flexible for end users
- Adds server-side state management complexity

**DECISION: Proceed with Option A** - Frontend-driven for maximum flexibility and user control.

## Detailed Implementation Plan

### Phase 1: Backend API Changes

#### 1.1 Update OpenRouter Service
**File**: `backend/services/openrouter.py`

**Changes:**
- Remove hardcoded `MODEL_ID` constant
- Add `model` parameter to `__init__()` method with sensible default
- Pass model to `stream_completion()` and `complete()` methods
- Update docstrings

**Code changes:**
```python
# Remove: MODEL_ID = "anthropic/claude-opus-4-5-20251101"

class OpenRouterService:
    def __init__(self, api_key: str, model: str = "anthropic/claude-opus-4-5-20251101"):
        self.api_key = api_key
        self.model = model  # Store as instance variable
        # ... rest of __init__

    async def stream_completion(self, ...):
        payload = {
            "model": self.model,  # Use instance variable
            # ... rest of payload
        }
```

#### 1.2 Update Request Schemas
**File**: `backend/models/schemas.py`

**Changes:**
- Add optional `model` field to all request schemas that use OpenRouter:
  - `LineExplainRequest`
  - `RangeExplainRequest`
  - `ArchitectureRequest`
  - `ChatRequest`

```python
class LineExplainRequest(BaseModel):
    api_key: str
    model: str = Field(
        default="anthropic/claude-opus-4-5-20251101",
        description="OpenRouter model ID to use"
    )
    repo_id: str
    # ... rest of fields
```

#### 1.3 Update Route Handlers
**Files**:
- `backend/routers/explain.py`
- `backend/routers/chat.py`

**Changes:**
- Pass `request.model` when creating `OpenRouterService` instances
- Update WebSocket handlers to extract model from request JSON

```python
# In explain.py:
service = OpenRouterService(request.api_key, request.model)

# In WebSocket handlers:
model = request.get("model", "anthropic/claude-opus-4-5-20251101")
service = OpenRouterService(api_key, model)
```

### Phase 2: Frontend State Management

#### 2.1 Update Zustand Store
**File**: `frontend/src/store/codeStore.ts`

**Changes:**
- Add `selectedModel` state
- Add `availableModels` configuration
- Add setters and persistence
- Define model interface

```typescript
export interface ModelOption {
  id: string
  name: string
  provider: string
  description: string
  contextWindow?: number
  recommended?: boolean
}

interface CodeStore {
  // Existing fields...

  // Model selection
  selectedModel: string
  availableModels: ModelOption[]
  setSelectedModel: (modelId: string) => void
  addCustomModel: (model: ModelOption) => void
  removeCustomModel: (modelId: string) => void
}

// In persist():
partialize: (state) => ({
  apiKey: state.apiKey,
  githubToken: state.githubToken,
  isDarkMode: state.isDarkMode,
  selectedModel: state.selectedModel,
  availableModels: state.availableModels, // Persist custom models
})
```

#### 2.2 Define Default Model List
**File**: `frontend/src/config/models.ts` (NEW)

```typescript
export const DEFAULT_MODELS: ModelOption[] = [
  {
    id: "anthropic/claude-opus-4-5-20251101",
    name: "Claude Opus 4.5",
    provider: "Anthropic",
    description: "Most capable model, best for complex code",
    contextWindow: 200000,
    recommended: true
  },
  {
    id: "anthropic/claude-sonnet-4-5",
    name: "Claude Sonnet 4.5",
    provider: "Anthropic",
    description: "Balanced performance and speed",
    contextWindow: 200000
  },
  {
    id: "openai/gpt-5-2-pro",
    name: "GPT-5.2 Pro",
    provider: "OpenAI",
    description: "Latest GPT model",
    contextWindow: 128000
  },
  {
    id: "google/gemini-3-0-pro",
    name: "Gemini 3.0 Pro",
    provider: "Google",
    description: "Google's advanced model",
    contextWindow: 100000
  },
  {
    id: "anthropic/claude-haiku-4",
    name: "Claude Haiku 4",
    provider: "Anthropic",
    description: "Fastest, most economical",
    contextWindow: 200000
  }
]
```

### Phase 3: UI Components

#### 3.1 Update SetupModal
**File**: `frontend/src/components/setup/SetupModal.tsx`

**Changes:**
- Add model selection dropdown
- Show model description
- Visual indicator for recommended model
- Keep it simple in setup (can configure more in settings)

**New section after GitHub token:**
```tsx
{/* Model Selection */}
<div className="space-y-2">
  <label className="flex items-center gap-2 text-sm font-medium">
    <Sparkles className="w-4 h-4 text-ct-primary" />
    AI Model
  </label>
  <select
    value={selectedModel}
    onChange={(e) => setSelectedModel(e.target.value)}
    className="w-full px-4 py-3 bg-ct-bg border border-ct-border rounded-lg text-sm focus:outline-none focus:border-ct-primary"
  >
    {availableModels.map(model => (
      <option key={model.id} value={model.id}>
        {model.name} {model.recommended ? '⭐ Recommended' : ''}
      </option>
    ))}
  </select>
  <p className="text-xs text-ct-text-secondary">
    {availableModels.find(m => m.id === selectedModel)?.description}
  </p>
</div>
```

#### 3.2 Create Model Management Component (NEW)
**File**: `frontend/src/components/settings/ModelSettings.tsx`

**Purpose**: Advanced model configuration
- Display all available models in a card grid
- Show model details (provider, context window, cost info)
- Add custom models via form
- Edit/remove custom models
- Import/export model configurations

**Features:**
```tsx
<ModelCard
  model={model}
  isSelected={model.id === selectedModel}
  onSelect={() => setSelectedModel(model.id)}
  onEdit={model.isCustom ? handleEdit : undefined}
  onDelete={model.isCustom ? handleDelete : undefined}
/>

<AddCustomModelForm
  onAdd={(model) => addCustomModel(model)}
/>
```

#### 3.3 Add Settings Modal/Page
**File**: `frontend/src/components/settings/SettingsModal.tsx` (NEW)

**Sections:**
1. API Configuration (move from SetupModal)
2. Model Selection (embed ModelSettings component)
3. UI Preferences
4. Advanced Options

**Access:**
- Settings icon in header
- Keyboard shortcut (Cmd/Ctrl + ,)

### Phase 4: API Integration

#### 4.1 Update API Calls
**Files to update:**
- `frontend/src/components/code/CodeEditor.tsx`
- Any component making API calls to explanation/chat endpoints

**Changes:**
- Include `selectedModel` from store in all API requests
- Pass model in WebSocket connections

```typescript
// Example in CodeEditor:
const { apiKey, selectedModel, repoId } = useCodeStore()

const response = await fetch('/api/explain/line', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    api_key: apiKey,
    model: selectedModel,  // Add this
    repo_id: repoId,
    // ... other fields
  })
})

// WebSocket example:
ws.send(JSON.stringify({
  api_key: apiKey,
  model: selectedModel,  // Add this
  // ... other fields
}))
```

### Phase 5: Model Information & Validation

#### 5.1 Model Info Display
**Where:** Explanation panel, chat interface

**What to show:**
- Small badge showing current model
- Tooltip with model details
- Option to quickly switch models

```tsx
<div className="text-xs text-ct-text-secondary flex items-center gap-2">
  <span>Explained by</span>
  <button
    className="px-2 py-0.5 bg-ct-bg border border-ct-border rounded hover:border-ct-primary"
    onClick={openModelSelector}
  >
    {currentModel.name}
  </button>
</div>
```

#### 5.2 Error Handling
**Handle OpenRouter API errors:**
- Invalid model ID → Show error, suggest similar models
- Model not available → Fallback to default model
- Rate limits → Display clear message

```typescript
const handleModelError = (error: any) => {
  if (error.includes('model not found')) {
    toast.error(`Model "${selectedModel}" not found. Using default model.`)
    setSelectedModel(DEFAULT_MODELS[0].id)
  }
}
```

### Phase 6: Documentation & Testing

#### 6.1 Update Documentation
**Files to update:**
- `README.md` - Add model selection to features
- Create `docs/MODEL_CONFIGURATION.md` - Detailed guide

**Contents:**
- How to select a model
- How to add custom models
- OpenRouter model ID format
- Cost considerations
- Performance differences

#### 6.2 Testing Checklist
- [ ] Model selection persists across sessions
- [ ] Custom models can be added/removed
- [ ] API requests include selected model
- [ ] WebSocket connections use selected model
- [ ] Error handling for invalid models
- [ ] Default model fallback works
- [ ] Model info displays correctly
- [ ] Settings modal accessible and functional

## Migration Strategy

### For Existing Users
1. On first load after update, set `selectedModel` to hardcoded default
2. Show brief notification: "New feature: You can now choose different AI models in Settings!"
3. No breaking changes - existing functionality continues to work

### Backward Compatibility
- All model fields have defaults
- Backend accepts requests without model field
- Frontend gracefully handles missing model preference

## Future Enhancements

### Phase 7 (Optional): Advanced Features
1. **Model Recommendations**
   - Suggest models based on file type/complexity
   - "This file is complex, try Claude Opus for better explanations"

2. **Cost Tracking**
   - Display approximate costs per explanation
   - Monthly usage dashboard
   - Budget warnings

3. **Model Performance Metrics**
   - Track explanation quality (user ratings)
   - Response time tracking
   - Suggest fastest model for simple explanations

4. **OpenRouter Integration**
   - Fetch available models from OpenRouter API
   - Show real-time model status (operational/degraded)
   - Display current pricing

5. **Multi-Model Comparison**
   - Get explanations from multiple models
   - Side-by-side comparison view
   - Vote on best explanation

## Implementation Timeline

### Sprint 1 (Backend Foundation)
- Day 1-2: Backend API changes
- Day 2-3: Update schemas and routers
- Day 3: Testing and documentation

### Sprint 2 (Frontend Core)
- Day 1-2: State management and model configuration
- Day 2-3: Update SetupModal
- Day 3-4: Update API integration points

### Sprint 3 (Advanced UI)
- Day 1-3: ModelSettings component
- Day 3-4: Settings modal/page
- Day 4-5: UI polish and testing

### Sprint 4 (Polish & Deploy)
- Day 1-2: Error handling and edge cases
- Day 2-3: Documentation
- Day 3-4: End-to-end testing
- Day 4-5: Deployment and monitoring

## Success Metrics

1. **Functionality**
   - Users can select from 5+ predefined models
   - Users can add custom models
   - Model preference persists

2. **UX**
   - Model selection takes <3 clicks
   - Clear model descriptions
   - No confusion about model choice

3. **Technical**
   - No breaking changes
   - All tests pass
   - Zero regression bugs

## Risk Mitigation

### Risk 1: Invalid Model IDs
**Mitigation:**
- Validate against OpenRouter on first use
- Cache valid models
- Clear error messages

### Risk 2: Model Deprecation
**Mitigation:**
- Monitor OpenRouter announcements
- Automatic fallback mechanism
- User notifications for deprecated models

### Risk 3: Performance Degradation
**Mitigation:**
- Lazy load model list
- Optimize state updates
- Monitor API response times

## Questions to Resolve

1. **Should we fetch available models from OpenRouter API?**
   - Pro: Always up-to-date
   - Con: Requires API call, adds dependency
   - **Recommendation:** Start with static list, add API fetch as Phase 7 enhancement

2. **Should we show pricing information?**
   - Pro: Helps users make informed decisions
   - Con: Pricing changes frequently
   - **Recommendation:** Add as optional Phase 7 feature with disclaimer

3. **Should model selection be per-repository or global?**
   - **Recommendation:** Global preference with per-session override option

4. **Should we validate model IDs client-side?**
   - **Recommendation:** No, let OpenRouter API handle validation for flexibility

## Conclusion

This implementation provides a robust, user-friendly model selection system that:
- ✅ Allows selection from popular models
- ✅ Supports custom model addition
- ✅ Persists user preferences
- ✅ Maintains backward compatibility
- ✅ Sets foundation for advanced features

The phased approach allows for incremental delivery and testing, with core functionality (Phases 1-4) providing immediate value while advanced features (Phases 5-7) can be added based on user feedback.
