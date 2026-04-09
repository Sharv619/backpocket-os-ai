# 🚨 SOP: The Emergency AI Handover (Switching Models)

If you need to switch AI assistants or continue development elsewhere:

**Option 1 (BEST — Free & Private): OpenCode + Ollama**
**Option 2 (Cloud Backup): Claude or ChatGPT**
**Option 3 (Swap Gemini key): Start a fresh Gemini session**

Read `docs/OPENCODE_TRANSITION.md` for the full step-by-step OpenCode setup guide.

> **Note:** This system is built and maintained using **OpenCode**. See `config/OPENCODE_SETUP.md` for configuration.

---

### Using OpenCode (Recommended)
1. Open a terminal in your `BackPocket_MVP` folder.
2. Type: `opencode`
3. Paste the "Brain Paste" block from `docs/OPENCODE_TRANSITION.md`.
4. OpenCode will read all your files and be ready in seconds.

### Using Claude / ChatGPT (Cloud Backup)
1. Open the file `PROJECT_CONTEXT.md` in your `BackPocket_MVP` folder.
2. Select everything (**Ctrl+A**) and copy it (**Ctrl+C**).
3. Open [Claude.ai](https://claude.ai) or ChatGPT.
4. Paste the text, then add at the top:
   > *"I am working on my BackPocket Twin project. Please read this context file to understand my current architecture, recent wins, and next steps. Once you've read it, let me know you're ready to continue working."*

---

### 💡 Why this works:
Because we keep `docs/` updated, any AI helper can get up to speed fast. They will know:
- The **Tier system** (T1-T5 rules, what gets archived vs stays in inbox).
- The **Batching** logic (so it doesn't break it).
- The **Ollama** fallback (so it knows you have a Mini-PC).
- The **Approval Rules** (no email ever sent without Cherry's WhatsApp approval).

**When you bring the work back to OpenCode later, just run `opencode` and continue — it reads the same files!** 🏁🍒

---

## 📝 Session Summary Template

At the end of each work session, update `SYSTEM_CONTEXT.md`:

```markdown
### YYYY-MM-DD - [Brief Title]
- ✅ [What was completed]
- ✅ [What was completed]
- ⚠️ [What was started but not finished]
- 📋 [Next steps / todo]
```

This keeps all docs in sync for the next session!
