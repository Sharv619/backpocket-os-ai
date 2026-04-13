# MCP Restructure Plan

**Date**: 2026-04-13
**Status**: Awaiting approval — no new files written yet
**Owner**: Claude + Sharv619

---

## Why

The repo evolved past its MCP setup. Specifically:

1. **Two parallel stacks** exist:
   - `src/mcp-wrapper/server.js` (Node, 13 tradie tools) — wired into `.mcp.json`
   - `mcp_servers/*.py` (Python twin servers) — **not referenced anywhere**, orphaned
2. **The Node server is broken**: `src/mcp-wrapper/package.json` declares `"type": "module"` but `server.js` uses CommonJS `require()`. It does not run today.
3. **Tool descriptions are verbose** — small local/instruct models (Ollama target) choke on heavy JSON schemas and 13 mixed-domain tools in one list.
4. **No shared knowledge bank** — teammates working on marketing/law/research branches have no common place to leave findings that AI tools can later cite (for audits).

## Goals

- One thin MCP server per domain so small models see a short, focused tool list per context.
- Zero-config setup for teammates: clone → `npm install` → open OpenCode → MCP just works.
- A shared "knowledge bank" (SQLite) with per-author attribution that auto-captures every merge into `main` as an audit-trail entry.

## Decisions (already made)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Keep Node stack, archive Python `mcp_servers/*.py` | Python twins are orphaned; Node is the live path |
| 2 | Split into 4 thin servers, not one monolith | Smaller tool lists = better small-model behavior |
| 3 | SQLite knowledge bank, not ChromaDB | Non-technical teammates shouldn't need vector DB install |
| 4 | Git attribution = SHA + author email | Cryptographically unique; GPG-ready if they opt in |
| 5 | Git hook is opt-in via `npm run setup-hooks` | Auto-installed hooks are invasive |

## Target Structure

```
mcp_servers/
  _archive_python/       ← old Python twins (moved, not deleted)
  _lib/
    mcp.mjs              ← stdio JSON-RPC handler (~40 lines, shared)
    db.mjs               ← promisified sqlite3 wrapper (~30 lines)
  leads.mjs              ← search_leads, create_lead, extract_lead_from_email
  quotes.mjs             ← create_quote, get_quote_template, match_quote_to_email, get_overdue_quotes
  pipeline.mjs           ← get_pipeline_summary, record_payment, suggest_next_action
  knowledge.mjs          ← save_note, search_notes, list_notes, get_note (common bank)
  package.json           ← ESM + sqlite3 dep

scripts/
  create_knowledge_table.py   ← migration for knowledge_notes table
  install-hooks.sh            ← symlinks git hooks into .git/hooks
  git-hooks/
    post-merge                ← auto-captures merges into knowledge bank

.mcp.json                ← registers all 4 mcp_servers/* as separate MCP servers
package.json             ← root; runs postinstall for mcp_servers/

src/mcp-wrapper/         ← DELETED (broken, superseded)
```

## knowledge_notes Schema

```sql
CREATE TABLE knowledge_notes (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  category      TEXT NOT NULL,          -- marketing | law | research | engineering | other
  title         TEXT NOT NULL,
  body          TEXT NOT NULL,
  tags          TEXT,                   -- comma-separated
  author_name   TEXT,                   -- from git config
  author_email  TEXT,                   -- from git config
  branch        TEXT,                   -- branch merged from
  commit_sha    TEXT,                   -- merge commit SHA (digital signature)
  source        TEXT DEFAULT 'manual',  -- 'manual' | 'auto_merge'
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_category ON knowledge_notes(category);
CREATE INDEX idx_knowledge_author ON knowledge_notes(author_email);
CREATE INDEX idx_knowledge_branch ON knowledge_notes(branch);
```

## post-merge Hook Behaviour

On every merge into `main`:

1. Read `git log -1` → commit SHA, author name, author email, subject, body
2. Read `git diff --name-only HEAD~1 HEAD` → files changed
3. Infer category from branch name prefix: `marketing/*` → marketing, `law/*` → law, `research/*` → research, otherwise `engineering`
4. Insert row: title=commit subject, body=commit body + files list, tags=categories from paths, signature fields filled
5. Print one-line confirmation to terminal

Teammates can also call `save_note` via MCP at any point to drop ad-hoc findings into the bank.

## .mcp.json (target)

```json
{
  "mcpServers": {
    "backpocket-leads":     { "command": "node", "args": ["./mcp_servers/leads.mjs"] },
    "backpocket-quotes":    { "command": "node", "args": ["./mcp_servers/quotes.mjs"] },
    "backpocket-pipeline":  { "command": "node", "args": ["./mcp_servers/pipeline.mjs"] },
    "backpocket-knowledge": { "command": "node", "args": ["./mcp_servers/knowledge.mjs"] }
  }
}
```

Dropped: `@modelcontextprotocol/server-gmail`, `server-google-drive`, `server-google-maps` — these require cloud keys and bloat the tool list. Gmail/Drive calls stay inside Python/FastAPI where they already work; MCP doesn't need to duplicate them.

## Execution Order

1. ✅ Archive `mcp_servers/*.py` → `mcp_servers/_archive_python/` (**done**)
2. ⏳ Create `mcp_servers/_lib/mcp.mjs`
3. ⏳ Create `mcp_servers/_lib/db.mjs`
4. ⏳ Create `mcp_servers/leads.mjs`
5. ⏳ Create `mcp_servers/quotes.mjs`
6. ⏳ Create `mcp_servers/pipeline.mjs`
7. ⏳ Create `mcp_servers/knowledge.mjs`
8. ⏳ Create `mcp_servers/package.json`
9. ⏳ Create `scripts/create_knowledge_table.py` + run it
10. ⏳ Create `scripts/git-hooks/post-merge` + `scripts/install-hooks.sh`
11. ⏳ Create root `package.json` with postinstall
12. ⏳ Overwrite `.mcp.json`
13. ⏳ Delete `src/mcp-wrapper/`
14. ⏳ Manual test: `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node mcp_servers/leads.mjs`
15. ⏳ Commit

## Open Questions for Sharv

- [ ] Confirm "happy instance" meaning (background agent / remote scheduled agent / resumable plan-doc)
- [ ] Any tools to keep from the old `server.js` that aren't in the target tool list? (e.g., `calculate_job_distance`, `estimate_travel_time`, `draft_follow_up_email`, `get_job_patterns`, `get_client_history`, `suggest_next_action` — I dropped `calculate_job_distance` and `estimate_travel_time` because they were mock/Maps-dependent, and rolled `draft_follow_up_email` / `suggest_next_action` / `get_job_patterns` / `get_client_history` into the Python backend since they're AI-prompt heavy. Confirm you're OK with that.)
- [ ] OK to delete `src/mcp-wrapper/` entirely, or archive alongside Python?

## Rollback

Everything is reversible:
- Python twins: `mv mcp_servers/_archive_python/*.py mcp_servers/`
- New Node files: `rm mcp_servers/*.mjs mcp_servers/_lib -rf`
- `.mcp.json`: restore from git (`git checkout .mcp.json`)
- `src/mcp-wrapper/`: restore from git if deleted
