---
name: ollama-integration-phase2
description: Complete mapping of Ollama integration for Phase 2 (provider selection, model management, prompts, failure handling, request details)
metadata:
  type: reference
---

# Ollama Integration — Complete Phase 2 Mapping

## 1. Provider Selection
- **UserDefaults key:** `selectedAIProvider` (AIService.swift:203, AIService.swift:301-306)
- **Endpoint configurability:** Yes — `ollamaBaseURL` UserDefaults key (OllamaService.swift:11, AIProvider.baseURL:49)
- **Default endpoint:** `http://localhost:11434` (OllamaService.swift:6, OllamaClient.swift:12)
- **UI for provider selection:** ProviderLocalManagementView.swift (VoiceInk/Views/AI\ Models/), shows Ollama radio row with "Connecting" / "Disconnected" / "N models" status (lines ~33-87)
- **Provider enum:** AIService.swift:4-19 (ollama case at line 17)
- **connectedProviders filter:** AIService.swift:234-250 (ollama is connected if ollamaService.isConnected)

## 2. Ollama Model Selection
- **UserDefaults key:** `ollamaSelectedModel` (OllamaService.swift:17, AIProvider.defaultModel:82)
- **Model list endpoint:** `/api/tags` (OllamaClient.swift:39)
- **Where list is fetched:** OllamaClient.fetchModels() (line 38), called from OllamaService.refreshConnectionAndModels() (line 62)
- **UI to select model:** ProviderLocalManagementView.swift (lines ~130-142), Picker over availableModels with onChange to updateSelectedOllamaModel()
- **Model filtering/validation:** OllamaClient returns [OllamaModel] with name field (line 105); no validation beyond checking name exists (OllamaService.swift:66-68)
- **Model reads:** OllamaService.selectedModel (line 15-19), persisted to UserDefaults via didSet; AIService.availableModels() for provider=ollama returns ollamaService.availableModels.map {$0.name} (line 287)

## 3. Prompts (CustomPrompt)
- **Storage format:** CustomPrompt.swift:4-49 — Codable struct with fields: id: UUID, title: String, promptText: String, useSystemInstructions: Bool
- **UserDefaults storage:** `customPrompts` key, as JSON-encoded [CustomPrompt] (AIEnhancementService.swift:43-45, 500-502)
- **Mode → Prompt reference:** ModeConfig.swift:75 `selectedPrompt: String?` (UUID string, not UUID itself; see ModeRuntimeConfiguration.swift:157)
- **Mode with no prompt selected + enhancement enabled:** repairModePromptSelections() (AIEnhancementService.swift:473-497) assigns first available prompt or nil
- **Prompt wrapper/system template:** AIPrompts.swift (lines 3-51) — `enhancementSystemTemplate` with hardcoded preamble:
  - "These instructions always apply"
  - "Turn the raw dictated speech inside <USER_MESSAGE>"
  - Lists default editing rules (fix transcription errors, punctuation, grammar, preserve meaning, apply self-corrections, etc.)
  - User's custom promptText inserted at line 39: `%@` (CustomPrompt.swift:44)
  - Custom vocabulary appended (AIEnhancementService.swift:137-149)
  - Context sections appended (AIEnhancementService.swift:154-162)

## 4. Per-Mode Enable
- **Toggle:** ModeConfig.swift:74 `isAIEnhancementEnabled: Bool`
- **UI to toggle:** ModeConfigFormView.swift (lines ~321-325), "AI Enhancement" Toggle in aiEnhancementSection
- **One mode can be on, another off:** Yes — each ModeConfig has independent isAIEnhancementEnabled (toggled per-mode in UI, stored in modeConfigurationsV2 UserDefaults)
- **Auto-provider assignment:** ModeConfigFormView.swift (lines ~326-334) if enhancement enabled but no provider selected, auto-selects first available from aiProviderOptions

## 5. Failure Path
- **enhance() called:** TranscriptionPipeline.swift:184-188, tries enhancement, catches at line 196
- **Raw transcript delivery on failure:** YES — finalText retains cleanedText value (set at line 151); catch block at 196-208 sets responseError but does NOT update finalText
- **Error handling in enhance():** AIEnhancementService.swift:404-424 (top-level enhance wraps makeRequestWithRetry), makeRequestWithRetry at 338-402 with 3 retries on network/server/rate-limit errors
- **Ollama-specific error handling:** AIEnhancementService.swift:203-224 calls aiService.enhanceWithOllama(), catches LocalAIError and re-throws as EnhancementError (timeout maps to EnhancementError.timeout, others to customError)
- **TranscriptionPipeline error handling:** line 196-208 shows notification with error.errorDescription (first 80 chars), sets transcription.enhancedText to "Enhancement failed: {error}", responseError for .respond mode
- **Request timeout (Ollama URLSession):** AIEnhancementService.swift:27-30 baseTimeout = 7 seconds default (UserDefaults EnhancementTimeoutSeconds), passed to OllamaService.enhance():209, passed to OllamaClient.generate():93, set on URLRequest.timeoutInterval:73 in OllamaClient.checkConnection(), 42 in fetchModels(), 93 in generate()
- **Slow model blocking:** Yes — a 30-second model response would block for 30s (OllamaClient.generate timeout is 30s default per line 69, but AIEnhancementService overrides with baseTimeout=7s or UserDefaults)

## 6. Streaming/Latency
- **API endpoint:** `/api/generate` (OllamaClient.swift:71), not `/api/chat`
- **Streaming:** No — `"stream": false` hardcoded (OllamaClient.swift:82)
- **Temperature:** 0.3 hardcoded (OllamaService.swift:25, default in OllamaClient.generate:67)
- **num_predict:** Not set (no max-tokens limit)
- **think parameter:** Optional (OllamaClient.swift:68, 84-86), pass `false` to disable, controlled by think: false in OllamaService.enhance():97
- **keep_alive:** Not set (no keep_alive in request body, OllamaClient.swift:77-86)
- **URLSession default timeout:** Used (OllamaClient uses URLSession.shared with per-request timeout set on URLRequest.timeoutInterval)

---

## Wiring Recommendation

**Can be set safely via UserDefaults edit (app closed):**
- `ollamaBaseURL` → endpoint URL (default "http://localhost:11434")
- `ollamaSelectedModel` → model name (default "mistral")
- `selectedAIProvider` → "Ollama" (if all other providers have keys/config, this selects Ollama)
- `EnhancementTimeoutSeconds` → timeout in seconds for all enhancement (7 default, applies to Ollama)
- `customPrompts` → JSON array of CustomPrompt (id UUID, title, promptText, useSystemInstructions)

**Must be set via UI (app running):**
- Provider selection (uses ObservableObject didSet to notify, refresh availability)
- Model selection from live /api/tags fetch (requires user to click "Connect" / "Refresh")
- Prompt creation/edit (manages CustomPrompt UUID references and Mode links)
- Per-mode isAIEnhancementEnabled and selectedPrompt (persisted in modeConfigurationsV2)
