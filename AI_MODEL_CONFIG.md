# AI Model Configuration - BackPocket OS

## Simple Explanation

**OpenRouter** = One dashboard for ALL AI models. Instead of signing up for Anthropic, OpenAI, Google separately, you use OpenRouter and it routes your request to the best model. Pay-as-you-go, unified billing.

**MCP (Model Context Protocol)** = How AI tools talk to external things (APIs, databases, your files). Think of it like "plug-ins" for AI.

---

## The Optimal Model Stack

| Task | Provider | Model | Why | Cost |
|------|----------|-------|-----|------|
| **Coding (Me)** | OpenRouter | Claude 3.5 Sonnet | Best for code, clear explanations | ~$3/1M tokens |
| **Email Triage** | Google Gemini | gemini-2.0-flash | Fast, cheap, great at categorization | Free tier (1280/day) |
| **Draft Writing** | Google Gemini | gemini-2.5-flash | Longer context, better writing | ~$0.075/1M |
| **Fallback/Private** | Ollama (local) | Qwen3-8B | FREE, runs on your Mini-PC | $0 (electricity) |
| **Heavy Tasks** | Ollama (GPU) | Qwen3-32B | Complex reasoning, OCR | $0 (electricity) |
| **Communication Coach** | OpenRouter | GPT-4o | Best for tone/style analysis | ~$5/1M tokens |
| **Voice Practice** | OpenAI | gpt-4o-mini-tts | Text-to-speech | ~$0.015/1M chars |

---

## How It Works in Practice

```
You: "Hey, fix the email triage bug"

     ↓
     
Me (Claude via OpenRouter): 
  → Reads your code
  → Understands the bug
  → Writes the fix
  → Tests it

     ↓

Twin (Gemini via Google API):
  → When running, triages emails
  → Falls back to Ollama if Gemini fails

     ↓

Communication Coach (GPT-4o via OpenRouter):
  → Reviews all drafts
  → Scores confidence
  → Suggests power version
```

---

## Provider Setup Checklist

### Already Have ✅
- [x] Google Gemini API key (in .env as GEMINI_API_KEY)
- [x] Ollama running locally (on BB-Desktop)

### Need to Set Up 🔧
- [ ] OpenRouter account (https://openrouter.ai)
  - Get API key
  - Add to .env as OPENROUTER_API_KEY
  - Load $10 credit (lasts months)

### Optional (Later)
- [ ] ElevenLabs for voice (better than gpt-4o-mini-tts)
- [ ] Deepgram for speech-to-text (voice practice)

---

## .env Current Setup

```bash
# OpenRouter (for Claude & GPT-4o) ✅ CONFIGURED
OPENROUTER_API_KEY=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

# Local AI (Ollama) ✅ CONFIGURED
OLLAMA_MODEL=deepseek-r1:1.5b
OLLAMA_BASE_URL=http://localhost:11434/api/generate

# Optional: Voice
# ELEVENLABS_API_KEY=xxxxxxxxxxxxx
# DEEPGRAM_API_KEY=xxxxxxxxxxxxx
```

---

## Model Routing Logic (Auto-Select)

```
Task Type → Best Model → Fallback

Coding/Architecture → Claude 3.5 Sonnet → GPT-4o → Gemini
Email Categorization → Gemini → Ollama (Qwen3-8B)
Document Processing → Ollama (Qwen3-32B) → Gemini
Draft Review → GPT-4o → Claude → Gemini
Voice Practice → gpt-4o-mini-tts → Edge TTS (free)
```

---

## Performance Notes

| Model | Speed | Quality | Cost | Privacy |
|-------|-------|---------|------|---------|
| Claude 3.5 Sonnet | Fast | ⭐⭐⭐⭐⭐ | $$ | Cloud |
| GPT-4o | Fast | ⭐⭐⭐⭐⭐ | $$$ | Cloud |
| Gemini 2.0 Flash | Very Fast | ⭐⭐⭐⭐ | Free/$ | Cloud |
| Qwen3-8B (Ollama) | Fast | ⭐⭐⭐ | Free | 100% Local |
| Qwen3-32B (Ollama) | Medium | ⭐⭐⭐⭐ | Free | 100% Local |

**Strategy:** Use local AI for everything possible (free + private), cloud AI for complex tasks.

---

*Last Updated: 2026-03-27*
