# PROJECT ORCHESTRATOR
For debugging ALWAYS USE .claude/skills/bughunter (root-cause-analysis.md + SKILL.md)
## Active Phase Routing

**BEFORE any type of work, load the correct skill from .claude/skills and mention which skill is activated e.g. "/phase5-development activated" so I know that you actually launched the skill:**

| Phase | Skill to Load | Trigger |
|-------|--------------|---------|
| 2 | `/phase2-architecture` | Tech stack, architecture, security |
| 5 | `/phase5-development` | Coding sprints |
| 6 | `/phase6-qa` | Testing, QA |

**Cross-cutting skills (use anytime):**
- `/search-first` — Research protocol (online sources, version checking) use Context7 if needed
- `/log-update` — ALWAYS pdate contextlog.md After finishing a task.. and buglog.md after finding a bug and update it again after fixing that bug

## Core Rules (Always Active)

### No Guessing
- Don't know → say so, log gap. Unsure → state confidence %, flag for verification.
- Ambiguous → stop, write assumption, get confirmation. Challenge false premises.

### Search-First
- Before claiming any tool/lib/technique is "best" → search online. Latest stable versions only. use context7 if needed
- Include source URLs. State confidence.

### No Hacks
- Root causes, not symptoms. Production-grade only. Need more time → flag to user.
- **Requirements-first debugging:** Before proposing any fix, read the requirements section for the broken area. Generic patterns (circuit breakers, exponential backoff, extra retries, timeout adjustments) can violate the spec — e.g. if requirements say "retry once then surface to user", adding a 3-retry backoff loop contradicts that. Always anchor fixes to what the spec says, not to generic "best practice".

### Code Standards (Phase 5+)
See `/phase5-development` skill for full standards (SOLID, security, testing, API, git, coding, any task that involves planning the code, debugging or solving an issue in the code or project structure).
- Every PR must pass: lint + type check + unit tests + security scan
- Use /frontend-design when needed

### Server & Dev Lifecycle
- **Never start a server, dev process, or watcher.** The user owns all running processes.
- After any implementation, give brief run instructions instead:
  - Pre-steps first (migrations, seed, build, env setup — only what's needed)
  - Exact commands per terminal, numbered if multiple terminals are required
  - Example: "1. `pnpm db:migrate` → 2. terminal 1: `pnpm dev:server` · terminal 2: `pnpm dev:client`"

### Critical Defaults (most-forgotten)
- **pnpm always** — never npm/yarn. Commit `pnpm-lock.yaml`.
- **Orval** for API clients when an OpenAPI spec exists — never hand-write fetch wrappers.
- **Idempotency** — mutating endpoints must be safe to call twice. No double-charges, no duplicate records.
- **UTC in DB** — store timestamps in UTC; convert to local timezone on the frontend only.
- **No PII in logs** — no passwords, emails, tokens, or card numbers. Ever.
- **No direct push to main** — PRs + CI required. No exceptions.

### Logging Protocol
- `.claude/logs/contextlog.md` — ONGOING / DONE / LEFT / BLOCKED (after every task)
- `claude/logs/buglog.md` — Bugs + root-cause fixes (Phase 5+)
- Blocking items → log immediately → continue non-blocked work

### Report & Limitations Tracking (ML Projects — Always Active)
After finishing **any** implementation task, append a short entry to both files below. These are living documents — not a final report, just running notes that build up into one. Keep language plain, explain every acronym on first use per file, and keep each entry under 10 lines.

**`docs/report_progress.md`** — What was done, why it was done that way, what result it produced.
Entry format:
```
## [Task name] — [date]
**What:** one sentence describing what was built or run.
**Why:** one sentence on the design choice (e.g. "Used EfficientNetB0 because it runs fast on CPU").
**Result:** key number or outcome (e.g. "Validation accuracy: 94.2%, Recall: 96.1%").
**Acronyms used:** list any new acronyms with a one-line explanation.
```

**`docs/model_limitations.md`** — Honest notes on what the model can't do well yet, and how it could be improved.
Entry format:
```
## [Task name] — [date]
**Limitation found:** one sentence describing the gap.
**Why it happens:** brief technical reason in plain English.
**How to fix it (future):** one or two concrete suggestions.
```

Both files are committed alongside code. Never delete old entries — only append.

## Opus Advisor (Rare — Sonnet Handles 90%+)
Use `Agent(model: "opus")` ONLY for Super hard tasks that require deep reasoning or better planning.

## Token Efficiency (Always Active)
- **Read files:** ALWAYS Grep first to find line numbers, then Read with `offset` + `limit`. Never read full files unless <50 lines.
- **AWLAYS Suggest /compact:** Proactively tell the user to `/compact` after completing a sub-task, before switching focus, or when context feels heavy. Include what to focus the compact on (e.g., "use /compact now focus on: files modified, current blockers, next step").
- **WebSearch:** ONLY when user explicitly requests OR when checking library/API versions. Never for general coding questions.
- **Command output:** Capture brief simplified summaries, not full logs. Pipe through `head`/`tail` when possible.

## Session Discipline
- One focused task per session.
- `/compact` after each sub-task. `/clear` when switching phases.
- `/memory` audit at session start — prune stale notes.
- **At session close:** did we learn something reusable? → update MEMORY.md + relevant skill before `/compact`.


<!-- nx configuration start-->
<!-- Leave the start & end comments to automatically receive updates. -->

## General Guidelines for working with Nx

- For navigating/exploring the workspace, invoke the `nx-workspace` skill first - it has patterns for querying projects, targets, and dependencies
- When running tasks (for example build, lint, test, e2e, etc.), always prefer running the task through `nx` (i.e. `nx run`, `nx run-many`, `nx affected`) instead of using the underlying tooling directly
- Prefix nx commands with the workspace's package manager (e.g., `pnpm nx build`, `npm exec nx test`) - avoids using globally installed CLI
- You have access to the Nx MCP server and its tools, use them to help the user
- For Nx plugin best practices, check `node_modules/@nx/<plugin>/PLUGIN.md`. Not all plugins have this file - proceed without it if unavailable.
- NEVER guess CLI flags - always check nx_docs or `--help` first when unsure

## Scaffolding & Generators

- For scaffolding tasks (creating apps, libs, project structure, setup), ALWAYS invoke the `nx-generate` skill FIRST before exploring or calling MCP tools

## When to use nx_docs

- USE for: advanced config options, unfamiliar flags, migration guides, plugin configuration, edge cases
- DON'T USE for: basic generator syntax (`nx g @nx/react:app`), standard commands, things you already know
- The `nx-generate` skill handles generator discovery internally - don't call nx_docs just to look up generator syntax


<!-- nx configuration end-->