---
title: AGENTS.md / CLAUDE.md Staleness-Prevention System
status: planning — researching prior art
owner: garyj
started: 2026-05-24
last-updated: 2026-05-25
---

# AGENTS.md / CLAUDE.md Staleness-Prevention System

A living plan for solving the problem of stale agent-config files (AGENTS.md / CLAUDE.md / .cursor/rules.md / GEMINI.md) across many fast-changing solo-dev projects. This doc is iterated as more prior-art systems are researched.

## Pain we're solving

- Solo dev, multiple fast-changing projects (Django app → adds MCP → adds A2A, etc.)
- Agent-config files go stale because they only get updated when remembered, which is never
- **Silent failure mode**: can't see when Claude / Codex / Gemini read an outdated file and act on it
- Outdated config is **worse than absent** — the agent confidently follows wrong rules
- Efficiency matters more than completeness because it's a solo operation

## Architecture (4 layers, independently shippable)

```
┌─────────────────────────────────────────────────────────┐
│  CAPTURE          Stop hook + reflector (Cole pattern)  │ ← Phase 1
│  (in-session)     Writes timestamped proposals          │
├─────────────────────────────────────────────────────────┤
│  APPLY            /agents-review slash command          │ ← Phase 1
│  (on next start)  SessionStart surfaces N pending       │
├─────────────────────────────────────────────────────────┤
│  AUTHOR           /surgical skill (manual, hierarchy-   │ ← Phase 2
│  (when you know)  aware, contradiction-checked)         │
├─────────────────────────────────────────────────────────┤
│  AUDIT            Canary + scheduled weekly drift check │ ← Phase 3
│  (periodic)       Alderson-style JSONL mining           │ ← Phase 4
└─────────────────────────────────────────────────────────┘
```

Composes with existing setup:

- `/reagents` (built) — bulk restructure when a file gets too messy
- Auto-memory (`~/.claude/projects/.../memory/`) — cross-session knowledge of garyj (separate scope)
- `ce-compound` — solved-problem docs in `docs/solutions/` (separate scope)
- This system — continuous prevention of staleness in the agent-config files themselves

## Phase 1 — Capture + Apply (MVP)

**Goal:** Cole's pattern, deployed globally via chezmoi, with the four gaps fixed.

### Files (all chezmoi-managed)

```
~/.claude/settings.json                    ← Stop + SessionStart hooks
~/.local/bin/agents-reflect-trigger        ← cheap filter (Python)
~/.local/bin/agents-reflect                ← LLM reflector (Python)
~/.local/bin/agents-show-pending           ← SessionStart surfacing
~/.claude/commands/agents-review.md        ← slash command for review
```

### Trigger script (Cole + fixes)

Inherits Cole's design:
- `os.walk` for AGENTS.md / CLAUDE.md areas (layout-agnostic)
- git diff scoped to touched areas
- SHA256 fingerprint of scoped diff for dedup
- Recursion guard via env var (`AGENTS_REFLECT_LOCK`, generic name — not Cole's repo-specific one)
- Detached background spawn

Garyj-specific additions:
- Skip if PWD is `$HOME` / `~/.agents/` / `~/.claude/` (per reagents scope rules)
- Opt-out via `.claude/no-reflect` file in repo
- Daily cost budget at `~/.local/share/agents-reflect/budget-YYYY-MM-DD` — refuse if cap exceeded
- Codex / Gemini parallel: also fire on Codex's Stop hook if installed

### Improvements over Cole's reflector

| Cole | Ours |
|---|---|
| Writes `.claude/claude-md-review.md` (overwrites) | Writes `.claude/agents-proposals/<ISO-timestamp>.md` (queue) |
| No proposal lifecycle | Each file has frontmatter: `status: pending\|accepted\|rejected\|superseded` |
| SessionStart silent on proposals | Prints `📝 N pending proposals — /agents-review` |
| Hard-coded `uv` in command | Pure `python3` (or detect via shebang) |
| Single review file | One file per reflection event; `/agents-review` consolidates |

### Reflection prompt (lifted from Cole, tightened)

```
You are auditing whether <PROJECT>'s agent-config files still match reality
after a coding session. Below is the git diff of uncommitted changes, then
the current content of every AGENTS.md/CLAUDE.md for areas that changed.

For EACH area, output exactly one of:
  - "No change needed" — diff doesn't introduce anything the file should capture
  - A concrete proposed edit: lines to add/change/remove + one sentence why

Only propose when the diff introduces a genuine new convention, gotcha,
command, or constraint that the agent-config file does not yet capture.

IMPORTANT GUARDRAILS:
  - Do NOT propose sprint context ("currently migrating", "in progress on X").
    Only invariants — things that will still be true in 6 months.
  - Do NOT propose stylistic rewrites or reorganization.
  - If the file is already over 100 lines, suggest moving content to a
    subdirectory AGENTS.md or extracting to a skill — don't add more bullets.
  - Be terse. Plain text. No tool use.
```

### `/agents-review` slash command flow

```
Proposal 1/3 — 2026-05-24T22:14:08Z
File: pdj/CLAUDE.md
Reason: New env var MARKETBUDDY_API_TIMEOUT introduced — not documented

Proposed addition under "Project-specific gotchas":
+ `MARKETBUDDY_API_TIMEOUT` env var — defaults to 30s; tune for slow MongoDB

[a]pply / [r]eject / [d]efer / [s]urgical-edit
```

`s` hands off to `/surgical` (Phase 2) for placement / contradiction check.

## Phase 2 — `/surgical` skill (manual capture)

**Goal:** When you know you want to capture a rule (without waiting for the reflector), drop it in cleanly with hierarchy-aware placement.

Based on the [Claude Research artifact](file:///home/garyj/Downloads/compass_artifact_wf-c1ff9737-5d9b-4fb8-a862-9f5a91c0b644_text_markdown.md) with two changes:

1. Reuse `reagents` logic for hierarchy detection (already written + tested)
2. Add **line-count gate** — refuse to add if target file is already >100 lines; suggest `/reagents` first to split

The surgical skill becomes:
- Standalone command (`/surgical "<rule>" [target-file]`)
- The "apply" path used by `/agents-review` when proposals are accepted
- Always-available tool for manual capture

Files:
```
~/.agents/skills/surgical/SKILL.md
~/.agents/skills/surgical/placement-guide.md
```

## Phase 3 — Drift detection

**Goal:** Surface staleness even when the reflector misses it.

### 3a. Canary instruction (one line, deployed everywhere)

```markdown
<!-- canary: when you load this file, mention "ducktape" exactly once in your first reply -->
```

When the agent doesn't say "ducktape" → it's not loading the file. Cheapest possible silent-staleness detector. Source: [amattn.com](https://amattn.com/p/using_agentsmd_or_claudemd_to_counteract_agent_drift.html).

### 3b. Scheduled weekly drift audit per project

Use Claude's `/schedule` (reference_claude_triggers.md already tracks these). Per-project weekly audit:

1. Read AGENTS.md
2. Validate every command in the file still exists (`make <target>` resolves)
3. Validate every path mentioned still exists
4. Validate every env var mentioned is still referenced in code
5. Write findings to `.claude/agents-proposals/audit-YYYY-WW.md` as pending proposals

Catches the "commands listed silently broke 3 months ago" failure mode.

### 3c. (Optional) Alderson-style JSONL mining

Monthly batch — scan `~/.claude/projects/<project>/*.jsonl` for repeated user corrections. If garyj has told Claude "use `make pytest` not `uv run pytest`" five times in one project → that's an AGENTS.md proposal. Source: [martinalderson.com](https://martinalderson.com/posts/self-improving-claude-md-files/).

## Phase 4 — Cross-agent reality check

Garyj uses Claude Code, Codex, sometimes Gemini. Codex now supports hooks. Worth confirming the trigger script works as a Codex hook (pure Python, no Claude-specific deps). Gemini's hook story less mature — likely Claude-only initially.

## Open decisions

| # | Decision | Default | Why |
|---|---|---|---|
| 1 | Stop hook or SessionEnd? | **Stop with dedup** (Cole's choice) | SessionEnd misses crashes / force-quits; dedup makes Stop sane |
| 2 | Daily cost cap? | **$0.50/day** (configurable) | ~10 reflections @ Sonnet pricing |
| 3 | Proposals: queue or single file? | **Queue** (timestamped) | Cole's overwrite loses data on rapid sessions |
| 4 | Auto-apply or always review? | **Always review** | Garyj's AGENTS.md mandates plan-review on refactors |
| 5 | Per-repo opt-out marker? | **`.claude/no-reflect`** | Some repos (tries/, scratch/) shouldn't get this |
| 6 | Test repo for Phase 1? | **pdj** | Most familiar; easiest to evaluate proposal quality |
| 7 | Where do proposals live? | **`.claude/agents-proposals/` in-repo, gitignored** | Per-project, doesn't pollute commits |

## Explicit non-goals

- Auto-apply (even in yolo) — risk of bad proposals > friction of review
- Cross-machine proposal sync — solo dev on one laptop
- Team governance UI / DRI dashboards — solo dev
- PreCompact hook integration — unreliable per [GitHub #13572](https://github.com/anthropics/claude-code/issues/13572)
- Web UI for review — markdown + slash command is enough
- Custom LLM grader for proposal quality — use `claude -p`; if proposals are bad, fix the prompt

## Risks

1. **Proposal fatigue.** Low quality → ignored. Mitigation: aggressive trigger filter, conservative prompt, tune after a week of real use.
2. **Cost.** Capped, but watch the budget file the first month.
3. **Privacy.** Reflector sends git-diff + AGENTS.md content to `claude -p`. **Not** the transcript. Verify `.claudeignore` + settings.json `Read(./**/.env)` deny rule cover sensitive paths.
4. **Canary noise.** Agent saying "ducktape" every session = mild noise. Could move to quieter marker (HTML comment that asks for a specific tool call).
5. **Codex parity unknown.** Quick test needed before committing to chezmoi-managing it.

## Research summary

### Cole / helpline implementation (deep-dive 2026-05-24)

Repo: `/home/garyj/tries/2026-05-24-coleam00-helpline/`

**Architecture: two-process split.** Cheap deterministic trigger (`propose_claude_md.py`) decides whether to reflect; if yes, fires LLM reflector (`reflect_claude_md.py`) in a detached subprocess.

**Trigger logic (`propose_claude_md.py`):**
- `os.walk` finds every directory with a `CLAUDE.md` → these are the "areas" governed by the hierarchy
- `git status --porcelain` → maps each changed file to its nearest governing area
- If no areas touched → exit
- SHA256 fingerprint of `git diff HEAD -- <areas>` → stored in `.claude/.claude-md-review-state`
- If fingerprint matches prior → exit (dedup; Stop fires every turn)
- Else spawn reflector detached, return immediately
- Recursion guard via `HELPLINE_AILAYER_REFLECT_LOCK` env var (so nested `claude -p` doesn't re-trigger)
- Deterministic fallback if `claude` CLI missing — writes a "re-check these files by hand" note

**Reflector logic (`reflect_claude_md.py`):**
- Gathers scoped `git diff HEAD -- <areas>` (capped at 12,000 chars)
- Concatenates each touched area's `CLAUDE.md` as `### {area}/CLAUDE.md` blocks
- Calls `claude -p --output-format text` with reflection prompt (180s timeout)
- Writes to `.claude/claude-md-review.md` (overwrites each run)

**Elegant decisions:**
- Two-process split — turn never blocks
- Diff-scoped to touched areas only — unrelated changes don't drown the relevant ones
- Diff fingerprint keyed on scoped diff — reflection runs at most once per meaningful change
- Area-routing layout-agnostic — drop in any repo, works
- UTF-8 force on Windows consoles

**Fragilities (we fix):**
- `.claude/claude-md-review.md` overwritten each run — no queue, no history
- SessionStart `session_start_context.py` doesn't surface pending proposals — user must remember to check
- `HELPLINE_AILAYER_REFLECT_LOCK` repo-specific env name
- No cost cap (only dedup fingerprint + 180s timeout)
- `uv` hard-required in settings.json hook commands

**Other Cole artifacts worth noting:**
- `CODEBASE_MAP.md` — exactly the Anthropic article's "lightweight codebase map at root" pattern
- `AI-LAYER.md` — conceptual doc separating the meta-layer from the project's own CLAUDE.md
- Root `CLAUDE.md` is 41 lines and **doesn't reference the AI Layer system** — clean separation of concerns
- `.claudeignore` — 22 lines, sensible defaults
- `VALIDATION.md` — output of `tooling/validate/validate_all.py`, 13/13 checks proving article extension points work

### Community research (2026-05-25)

| Finding | Source | Why it matters |
|---|---|---|
| **200-line graveyard** — compliance halves as instructions double; practical ceiling ~60–100 lines for root files | [dev.to/minatoplanb](https://dev.to/minatoplanb/i-wrote-200-lines-of-rules-for-claude-code-it-ignored-them-all-4639) | A 250-line "fresh" file is already broken |
| **U-shaped attention** — top + bottom get weight, middle fades | Multiple | Drift detection must consider WHERE in the file a rule lives |
| **Canary instruction** — "say 'ducktape' when you read this" | [amattn.com](https://amattn.com/p/using_agentsmd_or_claudemd_to_counteract_agent_drift.html) | Cheapest silent-staleness detector |
| **Sprint context anti-pattern** — temporary state persists | [dev.to/ajbuilds](https://dev.to/ajbuilds/your-claudemd-is-probably-broken-5-silent-failure-patterns-and-how-to-fix-them-1abn) | Reflection prompt must filter sprint context |
| **PreCompact unreliable** — only fires on auto-compact | [GitHub #13572](https://github.com/anthropics/claude-code/issues/13572), [#43733](https://github.com/anthropics/claude-code/issues/43733) | Don't depend on PreCompact |
| **Prohibition-without-alternative freeze** — "never do X" without "instead do Y" causes Claude to stop and ask | dev.to/ajbuilds | Every prohibition needs paired alternative |
| **Dosu CI drift-detection lesson** — *"educational, not production-ready"* without a docs owner; no memory between runs | [dosu.dev](https://dosu.dev/blog/how-to-catch-documentation-drift-claude-code-github-actions) | Proposals need lifecycle state, not append-only |

### Adjacent / alternative systems

- **Alderson JSONL mining** ([martinalderson.com](https://martinalderson.com/posts/self-improving-claude-md-files/)) — mines `~/.claude/projects/*.jsonl` for repeated frustrations. Orthogonal to Cole's in-the-moment hook. *"30-second job per project"*.
- **mvara-ai precompact-hook** ([github](https://github.com/mvara-ai/precompact-hook)) — sends last 50 exchanges to a fresh subagent before compaction. *"Empty context can dedicate full attention to interpreting your session without the noise of its own history."* But PreCompact reliability issues limit this.
- **Karun multi-repo bootstrap** ([karun.me](https://karun.me/blog/2026/03/26/structuring-claude-code-for-multi-repo-workspaces/)) — manifest-driven root repo for multi-project workspaces. *"Tell Claude where to look rather than listing repos directly — lists go stale, source manifests don't."*
- **claude-md-improver** (Anthropic official) — bulk audit/improve across a codebase; no cross-file contradiction check
- **claude-diary** (Lance Martin) — `/reflect` command auto-updates CLAUDE.md; single-file, no hierarchy
- **claude-brain** (toroleapinc) — semantic merge across machines
- **agnix** (agent-sh) — 399-rule linter for agent config files

## Research log (to be appended as we go)

### 2026-05-24 — Cole's helpline repo
- Read `propose_claude_md.py`, `settings.json`
- Identified two-process split, fingerprint dedup, area-routing as the keepers
- Identified four fragilities to fix in our version

### 2026-05-25 — Cole reflector + community survey
- Deep-dive of `reflect_claude_md.py`, `session_start_context.py`, `AI-LAYER.md`, `CODEBASE_MAP.md`, `VALIDATION.md`
- Community survey across blog posts, GitHub issues, practitioner reports
- Surfaced 200-line graveyard, U-shaped attention, canary technique, PreCompact unreliability

### 2026-05-25 — entire.io (Thomas Dohmke / former GitHub CEO)

**Verdict: orthogonal — not a fit for our staleness pain. Steal one architectural idea, look at one sub-repo, skip as a replacement.**

**What it is:**
- Git-native Go CLI tool, MIT-licensed, free, fully self-hosted
- Captures AI agent sessions to a sidecar git branch (`entire/checkpoints/v1`)
- First product: "Checkpoints" — every session indexed alongside commits
- 4.4k stars on `entireio/cli` in ~3 months; 68 releases since Feb 2026 launch; real adoption
- Founded by **Thomas Dohmke** (GitHub CEO 2021–Aug 2025); $60M seed at $300M valuation Feb 2026, led by Felicis

**Mental model:** Git observability / audit layer for the agentic era. Dohmke's framing: *"AI agents produce code opaquely — the 'why' disappears."* Analogous to Ford's assembly line needing new instrumentation.

**Why it's orthogonal to our pain:**

| Entire's pain | Our pain |
|---|---|
| *"I don't know why this code was written this way"* | *"AGENTS.md goes stale, agents follow wrong rules"* |
| Looking **backward** at past sessions | Looking **forward** at agent inputs |
| Captures the artifact (transcript) | Updates the instructions (config) |

Entire has **zero mention** of AGENTS.md / CLAUDE.md / agent-config files across CLI README, blog posts, docs, roadmap.

**Ideas worth stealing:**
- **Sidecar git branch for metadata** — our staleness system could write proposals/audits to a `agents/staleness-reports` branch the same way: diff-triggered, never on main, always queryable, git-native lifecycle.

**Sub-repos worth a closer look (deferred):**
- [`entireio/skills`](https://github.com/entireio/skills) (174★) — *"Cross-agent skills that help coding agents use Entire context from Checkpoints, sessions, and git history to search past work, explain code, and hand off sessions."* Closest overlap with our context-passing problem. **15-min read worth doing.**
- [`entireio/pgr`](https://github.com/entireio/pgr) (46★) — *"experimental, stateless MCP code-search server for studying how ranking, latency, and output shaping affect agentic search."* Could feed our drift detection (what changed in the code that should update AGENTS.md?).
- [`entireio/git-sync`](https://github.com/entireio/git-sync) (454★) — unrelated to staleness; mirrors git refs without local checkout. Skip.

**Pricing:** Free, MIT, self-hosted, no account required, all data stays in repo. Solo-dev viable. Presumed future revenue: team/enterprise tier.

**Practitioner signal:** Too new (3 months) for deep consensus. Best independent label: OSTechNix calls it *"Git Observability Layer for AI Agents"* — accurate.

**Sources:**
- [Hello Entire World — launch post](https://entire.io/blog/hello-entire-world)
- [The Entire CLI: How It Works & Where It's Headed](https://entire.io/blog/the-entire-cli-how-it-works-and-where-its-headed)
- [Thomas Dohmke raises $60M — TechCrunch](https://techcrunch.com/2026/02/10/former-github-ceo-raises-record-60m-dev-tool-seed-round-at-300m-valuation/)
- [The New Stack interview](https://thenewstack.io/thomas-dohmke-interview-entire/)
- [OSTechNix review](https://ostechnix.com/entire-cli-git-observability-ai-agents/)

### 2026-05-25 — entireio/skills (sub-repo of Entire)

**Verdict: steal 5 patterns; does not address AGENTS.md staleness directly.**

The repo contains exactly 6 cross-agent skills, all built around Entire CLI's session-capture system:

| Skill | What it does |
|---|---|
| `explain` | Fetches the dev conversation that produced a function/line via git blame + checkpoint lookup |
| `search` | Full-text search across all stored session checkpoints |
| `session-crosslink` | Attaches a session to multiple repos' HEAD commits (parent-folder work) |
| `session-handoff` | Resumes prior session with structured 5-section summary; no clarifying questions |
| `session-to-skill` | Extracts a repeated workflow pattern into a new SKILL.md |
| `what-happened` | Git blame + checkpoint = "why was this line written" |

**Patterns worth stealing:**

1. **Structured handoff sections with conditional fields** — session-handoff's 5-section output (Task Overview / Current State / Discoveries / Next Steps / Context to Preserve) + a conditional "Unanswered Question" block that pauses continuation. Port to staleness reports: "Last Verified / Known Drift / Unresolved Questions / What Would Break If You Used This Now."
2. **Preview-then-confirm for destructive multi-file ops** — session-crosslink mandates a preview table before `entire session attach`. Our surgical skill should produce a diff table (file / current claim / proposed update / confidence) before writing.
3. **Graceful degradation with named fallback modes** — what-happened distinguishes "checkpoint-backed provenance" from "current-code fallback." For staleness: label evidence tiers ("verified against live state" / "inferred from git history" / "no signal — manual review").
4. **Extraction discipline — patterns, not transcripts** — session-to-skill: extract the durable claim, not the derivation. Preserve provenance (session, commit, date) as metadata, not as content.
5. **Token budget baked into the skill** — session-handoff caps at 8 sessions per checkpoint. Our staleness-scan should cap (max N files per run, max M changed lines before manual escalation).

**Sources:**
- [`session-handoff/SKILL.md`](https://raw.githubusercontent.com/entireio/skills/main/skills/session-handoff/SKILL.md)
- [`session-crosslink/SKILL.md`](https://raw.githubusercontent.com/entireio/skills/main/skills/session-crosslink/SKILL.md)
- [`session-to-skill/SKILL.md`](https://raw.githubusercontent.com/entireio/skills/main/skills/session-to-skill/SKILL.md)
- [`what-happened/SKILL.md`](https://raw.githubusercontent.com/entireio/skills/main/skills/what-happened/SKILL.md)

### 2026-05-25 — claude-diary (Lance Martin / LangChain)

**Verdict: steal the reflect prompt; do NOT adopt — dormant + broken.**

**What it is:** Claude Code plugin (MIT, Dec 2025) with two slash commands. `/diary` captures session work to `~/.claude/memory/diary/`; `/reflect` reads accumulated entries and proposes CLAUDE.md updates. Pre-compact.sh hook tries to auto-trigger `/diary` but is **broken** (Issue #2, unresolved). Last commit Dec 17 2025 — dormant 5 months. Single-CLAUDE.md by design (no hierarchy).

**How `/reflect` works:** 16KB markdown prompt, entirely LLM-driven, 12 sequential steps. Reads `processed.log` to skip already-analyzed entries → globs diary files → filters → reads existing CLAUDE.md → analyzes for rule violations AND new patterns → applies signal threshold → synthesizes across 6 categories → writes reflection file → overwrites CLAUDE.md → appends to processed.log.

**Patterns worth stealing (all 6 go into our Phase 1 reflector):**

1. **Signal threshold for codification** — quote: *"2+ occurrences = emerging pattern; 3+ = strong pattern; 1 = document but don't codify."* Prevents one-off sessions from bloating AGENTS.md.
2. **Rule violation detection as first-class pass** — before looking for *new* rules, scan for cases where *existing* rules were violated. Higher signal than pattern-finding; directly addresses staleness (a repeatedly-violated rule is either wrong or needs strengthening).
3. **`processed.log` deduplication** — track which diary entries (or in our case, diff fingerprints) have been reflected on. Trivial; makes the system idempotent.
4. **Context-first capture** — read current conversation without tool calls; fall back to JSONL parsing only when context is insufficient.
5. **Capture/consolidate split** — accumulate raw signal cheaply (`/diary`), run expensive analysis on demand (`/reflect`). Maps to our trigger/reflector split (already planned).
6. **Imperative, no-explanation rule format** — hard constraint in the prompt. Worth adopting for our own rule format.

**Practitioner extension worth knowing about:** [PGHH84/claude-layered-learning](https://github.com/PGHH84/claude-layered-learning) — built on claude-diary, adds hierarchy routing and end-of-session 4-phase flow. The hierarchy implementation is the missing piece in claude-diary itself.

**Sources:**
- [github.com/rlancemartin/claude-diary](https://github.com/rlancemartin/claude-diary)
- [Lance Martin blog post on Claude Diary](https://rlancemartin.github.io/2025/12/01/claude_diary/)
- [Issue #2 — pre-compact hook broken](https://github.com/rlancemartin/claude-diary/issues/2)
- [PGHH84/claude-layered-learning — practitioner fork with hierarchy](https://github.com/PGHH84/claude-layered-learning)

### 2026-05-25 — claude-md-improver (Anthropic official)

**Verdict: steal the scoring rubric verbatim; do not build on top.**

**What it is:** Skill in the official `claude-md-management` plugin (`anthropics/claude-plugins-official`, by Isabella He). **205,410 installs**, Anthropic Verified. Manual-trigger 5-phase workflow: discovery → quality assessment → report → diff proposal → apply. Companion command `/revise-claude-md` captures session learnings post-hoc.

**Trigger phrase (verbatim):** *"Use when user asks to check, audit, update, improve, or fix CLAUDE.md files. Also use when the user mentions 'CLAUDE.md maintenance' or 'project memory optimization'."*

**Scoring rubric (lift verbatim into our Phase 1):**

| Criterion | Weight |
|---|---|
| Commands/workflows documented | High |
| Architecture clarity | High |
| Currency (reflects current codebase) | High |
| Actionability (executable, not vague) | High |
| Non-obvious patterns / gotchas | Medium |
| Conciseness | Medium |

Scores per-file with letter grades (A: 90-100 → F: 0-29). Propose-then-confirm UX; updates additive by default; explicitly preserves existing structure.

**What it does NOT do (= what we still need to build):**
- No cross-file contradiction detection
- No hierarchy-aware inheritance checking
- No hook integration (manual-trigger only)
- No automated scheduling
- No command-existence verification (LLM judgment only, no shell-out to `make -n` or PATH lookup)
- No freshness timestamps / "last verified" metadata
- No AGENTS.md awareness (CLAUDE.md only)

**Why not extend it:** No programmatic API, no hooks, no inspectable intermediate state. Architecture is "LLM reads files and judges." Wrapping it as a subprocess gives us nothing.

**Sources:**
- [SKILL.md verbatim](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/claude-md-management/skills/claude-md-improver/SKILL.md)
- [/revise-claude-md command](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/claude-md-management/commands/revise-claude-md.md)
- [Plugin page on claude.com](https://claude.com/plugins/claude-md-management)

### 2026-05-25 — agnix (agent-sh)

**Verdict: integrate as pre-flight check. Catches structural staleness; semantic still on us.**

**What it is:** Rust linter (and LSP server) for agent config files. Validates CLAUDE.md, AGENTS.md, SKILL.md, MCP configs, hooks, settings.json across Claude Code, Codex CLI, Cursor, Kiro, GitHub Copilot, Cline, Gemini CLI, OpenCode. Ships as npm/Homebrew/Cargo + VS Code/JetBrains/Neovim/Zed plugins. **423 rules** (was 399 per prior research). **127 rules autofixable.**

**Rule taxonomy (~):**
- 40% syntax/format (malformed TOML, unclosed XML, frontmatter parse errors)
- 45% structural/schema (missing required fields, unknown keys, size limits, deprecated keys)
- 15% **semantic/cross-layer** — this is the interesting part

**Cross-layer rules (the ones we care about):**
- **XP-004**: *"Conflicting build/test commands detection (npm vs pnpm vs yarn vs bun)"* — fires when CLAUDE.md and AGENTS.md specify different package managers
- **XP-005**: *"Conflicting tool constraints detection (allow vs disallow across files)"* — fires when one file allows a tool another disallows, with no documented precedence
- **XP-006**: *"Multiple instruction layers without documented precedence warning"*
- **CDX-AG-004**: *"AGENTS.md contradicts config.toml"* (Codex)
- **CDX-CFG-029**: detects `agents.max_threads` set alongside `multi_agent_v2 = true` (feature incompatibility)

**Adoption:** 258★, 24 forks, 52 releases in 4 months, daily upstream rule watcher (auto-polls Claude Code / Codex / Kiro release notes to keep rules current). VS Code marketplace + Zed extension live. Active.

**How to integrate:**
```bash
# pre-commit hook
agnix --fix-safe .

# CI
agnix .
```

**Where it falls short for us:**
- Cannot detect semantic staleness ("CLAUDE.md says use mise for Python but project migrated to uv" — no rule violation)
- No knowledge of external ground truth (upstream tool versions, mise.lock state)
- Doesn't compare CLAUDE.md across time (no "this was accurate 6 months ago" concept)

**Verdict:** Use as cheap pre-flight gate. Catches the structural class for free. Build our semantic layer on top — don't conflate the 423 rules with staleness coverage.

**Sources:**
- [github.com/agent-sh/agnix](https://github.com/agent-sh/agnix)
- [docs site](https://agent-sh.github.io/agnix/)
- [CHANGELOG](https://github.com/agent-sh/agnix/blob/main/CHANGELOG.md)
- [VS Code marketplace](https://marketplace.visualstudio.com/items?itemName=avifenesh.agnix)

### 2026-05-25 — Karun multi-repo bootstrap

**Verdict: adopt the principle ("manifests not lists"). Optional structural adoption for `/home/garyj/dev/`.**

**The pattern:** A bootstrap repo containing only three things — a repo manifest (`mani.yaml`), a layered `CLAUDE.md` hierarchy (org / team / repo), and cross-repo task definitions. Subdirectory repos are gitignored using `dir/*` (not `dir/`) with `!dir/CLAUDE.md` exception so team-level configs are tracked but repo contents aren't.

**Key insight (the most important finding across all 5 systems):**

> *"This group's repos are defined in `mani.d/orders.yaml`. Each project has a `desc` field."*
>
> The org-level CLAUDE.md tells Claude *how to discover* repos (via the manifest file) rather than listing repo names inline. The manifest is the source of truth; the CLAUDE.md delegates to it.

And from his earlier post: *"Stale documentation lies confidently. It states things that are no longer true."*

**Generalization — "manifests not lists" inside a single project:**

| ❌ Goes stale | ✅ Stays fresh |
|---|---|
| `Services: auth-service, order-service, payment-service` | `Services defined in docker-compose.yml — read that` |
| `Dependencies: react 18.2, etc.` | `See package.json` |
| `Env vars: DATABASE_URL, REDIS_URL, ...` | `See .env.example` |
| `API routes: /users, /orders, ...` | `Routes in src/routes/*.ts — read directory` |
| `Feature flags: SHOW_X, ENABLE_Y` | `Flags in config/flags.yaml` |

Any list with an authoritative machine-readable home should be **referenced, not duplicated**.

**Proposed `/home/garyj/dev/` workspace structure (Phase 5):**

```
dev/
  mani.yaml               # workspace manifest
  CLAUDE.md               # org-level: "read mani.yaml for inventory"
  pdj/
    CLAUDE.md             # cluster-level: shared stack across pdj_*
    pdj/                  # gitignored — separate repo
    pdj_mcp/              # gitignored
    frontend/             # gitignored
    aws/                  # gitignored
  tries/
    CLAUDE.md             # "throwaway — no conventions enforced"
```

**Caveats:**
- No published Karun template — blog is the spec; build from scratch
- `mani` is lightly maintained; concepts apply with `mise`, a shell script, or plain `REPOS.md`
- Solo-dev value lower than team-scale value but principle still holds

**Sources:**
- [karun.me/blog/2026/03/26/structuring-claude-code-for-multi-repo-workspaces/](https://karun.me/blog/2026/03/26/structuring-claude-code-for-multi-repo-workspaces/)
- [karun.me/blog/2026/01/02/intelligent-engineering-in-practice/](https://karun.me/blog/2026/01/02/intelligent-engineering-in-practice/) (staleness quote)
- [github.com/alajmo/mani](https://github.com/alajmo/mani)
- [manicli.com](https://manicli.com/)

### [Next system to research goes here]

## Decision log (to be appended as we go)

### 2026-05-25 — Initial defaults
- Stop hook with dedup (not SessionEnd) — per Cole, validated
- Queue proposals, not overwrite — fix Cole's gap
- Always require human review — per garyj's AGENTS.md mandate
- Test in pdj first before chezmoi rollout
- Skip PreCompact hook — reliability issues

### 2026-05-25 — Post-prior-art-research decisions

After researching entireio/skills, claude-diary, claude-md-improver, agnix, Karun multi-repo:

- **Don't adopt claude-diary** (dormant 5 months, pre-compact hook broken). Lift its 6 reflect-prompt patterns into our Phase 1 reflector — write fresh.
- **Don't extend claude-md-improver** (no programmatic API, no hooks). Lift the 6-criterion scoring rubric verbatim.
- **Integrate agnix as Phase 3d pre-flight** (`agnix --fix-safe .` in pre-commit + weekly). Catches structural staleness; cheap; deterministic.
- **Adopt "manifests not lists" principle** (Karun) — applies to Phase 2 surgical skill (refuse to add inline lists when source-of-truth file exists) and to authoring guidance generally.
- **Add new Phase 5: Karun-style workspace structure** for `/home/garyj/dev/` — optional, orthogonal to staleness work, but synergistic.
- **Don't install Entire CLI for staleness purposes** — orthogonal. Install separately if session audit trails are wanted for their own sake.

### [Next decision goes here]

## Build status

| Phase | Status | Notes |
|---|---|---|
| Phase 1 — Capture + Apply | Not started | MVP target |
| Phase 2 — `/surgical` skill | Not started | Can be built in parallel with Phase 1 |
| Phase 3a — Canary instruction | Not started | Trivial; can ship with Phase 1 |
| Phase 3b — Scheduled drift audit | Not started | Depends on Phase 1 proposal infrastructure |
| Phase 3c — JSONL mining | Optional | Later |
| Phase 4 — Cross-agent (Codex/Gemini) | Not started | Test parity before chezmoi-managing |
