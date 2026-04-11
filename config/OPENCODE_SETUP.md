# BackPocket OS - OpenCode Configuration

## How to Use

Create a file called `.opencode.json` in your home directory:

### Windows
```
C:\Users\Cherry\.opencode.json
```

### Or set environment variable
```bash
OPENAI_API_KEY=your_openrouter_key_here
```

---

## Current Setup

| Setting | Value |
|---------|-------|
| Provider | OpenRouter |
| Default Model | Claude 3.5 Sonnet |
| Fallback Model | GPT-4o |
| API Key | sk-or-v1-85cd7aa1c4ce365... (masked) |

---

## Available Models (Top Picks)

| Model | Best For | Cost |
|-------|----------|------|
| `anthropic/claude-3.5-sonnet` | Coding, reasoning | ~$3/1M |
| `anthropic/claude-3.5-haiku` | Fast tasks | ~$0.80/1M |
| `openai/gpt-4o` | General purpose | ~$5/1M |
| `openai/gpt-4o-mini` | Fast, cheap | ~$0.15/1M |
| `google/gemini-2.0-flash` | Fast, free tier | Free/$0 |

---

## Cost Estimate (Monthly)

| Task | Model | Est. Usage | Cost |
|------|-------|------------|------|
| Coding (me) | Claude 3.5 Sonnet | 100K tokens | ~$0.30 |
| Communication Coach | GPT-4o | 50K tokens | ~$0.25 |
| **Total** | | | **~$0.55/month** |

*With 1M tokens free from OpenRouter signup, $10 credit = ~18 months!*

---

*Last Updated: 2026-03-27*
