---
name: reagents
description: Refactor a project's AGENTS.md / CLAUDE.md to be lean, hierarchical, and aligned with Anthropic's large-codebases guidance — splits per-service content into subdirectory files, extracts reusable expertise into skills, prunes stale model-compensation rules, and adds missing essentials (directory map, command scoping, gotchas). Use when an agent-config file is over ~100 lines, has internal contradictions or duplicate sections, mixes per-service content, or when the user says "refactor my AGENTS.md", "split this CLAUDE.md", "audit the agent config", "/reagents", or "/reclaude". Project-scoped only — refuse to run in $HOME, ~/.agents/, or ~/.claude/; those follow different rules.
---

# reagents

Refactor a project's `AGENTS.md` / `CLAUDE.md` (and friends like `.github/copilot-instructions.md`, `GEMINI.md`, `.cursor/rules.md`) so the root file is a thin pointer document and detail lives where it loads on demand. Grounded in Anthropic's [How Claude Code Works in Large Codebases](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start): *"root file for the big picture, subdirectory files for local conventions"*.

## When to refuse

This skill is **project-scoped only**. Refuse and explain if you find yourself:

- In `$HOME`, `~`, `~/.agents/`, `~/.claude/`, or any other home-level config tree. Those files are foundational and follow different rules — they layer *into* projects, not the other way round.
- In a directory that isn't a git repo, or in a repo with no agent-config file. The latter calls for `/init` (or a fresh draft), not a refactor.

## Flow

`Detect → Measure → Diagnose → Propose → Apply`. Each step has an early-exit: if nothing's wrong, say so and stop. Don't refactor a file that's already lean.

## 1. Detect

1. `git rev-parse --show-toplevel` to confirm a real repo. If it errors or points to a home-level path, refuse.
2. Find every agent-config file in the tree. Look for: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules.md`, and any nested `AGENTS.md`/`CLAUDE.md` in subdirectories. **Exclude** `.worktrees/`, `node_modules/`, `cdk.out/`, `build/`, `dist/`, `.venv/`, and any directory listed in `.gitignore` — these hold stale or generated copies that aren't the source of truth. Note symlinks — pdj-style `CLAUDE.md → .github/copilot-instructions.md` is one file, not two.
3. Survey the repo to inform recommendations: top-level directories, package manager(s), test/lint commands, and multi-service signals (subdirs with their own `pyproject.toml` / `package.json` / `Makefile`). For repos with more than ~20 top-level entries, spawn a read-only subagent to map structure — per Anthropic, *"spin up a read-only subagent to map a subsystem and write findings to a file"* keeps your editing context clean. The subagent should write a markdown directory map (top-level paths + one-line purpose each) to a temp file; you read it once and discard, rather than holding the raw `ls`/`tree` output in your own context.
4. **Note git submodules** (`git submodule status`). Submodules are separate repos with their own history and their own AGENTS.md needs — leave them alone. Don't propose creating or modifying agent-config files inside a submodule path; that's a separate refactor in the submodule's own repo.

## 2. Measure

Report line count and a one-paragraph structural read:

- **< 100 lines, clearly organized, no duplication** → stop. Report *"looks fine, no refactor needed"* and exit.
- **100–200 lines** → trim and reorganize in place; splitting probably isn't worth it.
- **> 200 lines, OR multi-service repo with service-specific content in root** → propose per-subdirectory `AGENTS.md` files in addition to trimming root.

The 100-line target is a guide, not a gate. A 130-line file with a clean directory map and good gotchas isn't a problem; a 90-line file full of stale rules is.

## 3. Diagnose

Walk the file and collect every issue *before* proposing changes. Don't fix as you go.

**Contradictions.** Rules that conflict (e.g., one says "always X", another says "never X"). Collect them all; resolve in one batched `AskUserQuestion` rather than asking one at a time. In yolo / non-interactive runs, default to the more conservative version and flag the choice in the output.

**Stale model-compensation rules.** Rules written to work around old-model limitations that current frontier models don't have — "always read in 100-line chunks", "you can't see images", "ask before calling a tool". Per the article, *"instructions compensating for old model limitations become overhead — review every 3–6 months"*. Flag these for removal with a one-line reason.

**Per-service content in a root file.** Sections that only apply to one app, service, or subdirectory. The win from moving them: per Anthropic, *"running the full suite when Claude changed one service causes timeouts"* — per-service files let Claude load only what's relevant. Identify candidates by any of these signals: (a) the section header names a subdirectory or service (`## Django apps`, `## Frontend`, `## MCP server`), (b) the content is gated by phrases like "when working on `<path>/`", or (c) every example, command, or convention in the section is scoped to one subtree. Topical headers without explicit gating are the common case — don't wait for "when working on" wording before flagging.

**Reusable expertise that belongs in a skill.** Multi-step workflows or domain how-tos that:
- Are substantial (>20 lines on one topic)
- Are more "how to do X well" than "where X lives here"
- Would apply across more than one project

The article: *"Skills solve this through progressive disclosure, offloading specialized workflows and domain knowledge. Not all expertise needs to be present in every session."* **Flag these as skill candidates only — don't try to extract them as part of the refactor.** Skill design (trigger description, scope, overlap with existing skills, content reframing) is its own exercise; recommend the user run `/document-skills:skill-creator` on each candidate when ready. Leave the content in place in AGENTS.md until that happens, so nothing is lost.

**Missing essentials.** A good project root file has:
- One-sentence project description
- **Where things live** — directory map, especially if the structure isn't self-evident
- **Commands** — build, test, lint, typecheck; per-service if multi-service
- **Gotchas** — non-obvious footguns (env vars, magic constants, integration quirks)
- **Glossary** — only if the domain has its own vocabulary
- **Verification** — what to run after changes (often a subset of Commands)

If any are missing, propose adding them. For Commands, scan `Makefile`, `justfile`, `package.json`, `pyproject.toml`, `composer.json`, etc., to discover real commands rather than guess.

**Outright bloat to remove.**
- Generic advice ("write clean code", "follow best practices")
- Restatements of language/framework basics the agent already knows
- Inline interface/type definitions duplicated from code
- Documentation that lives elsewhere (link instead)
- Personal preferences that belong in `~/.agents/AGENTS.md`, not the project file

## 4. Propose

Write a plan as a short markdown summary. Show it before touching files. Structure:

```
### Plan

**Root file** (was N lines → target M lines)
- Keep: <bulleted list>
- Add: <missing essentials>
- Remove: <bloat / stale rules with one-line reason each>

**Subdirectory files to create**
- `<path>/AGENTS.md` — <one-line summary of moved content>

**Skill candidates** (flagged for separate extraction via `/document-skills:skill-creator` — left in AGENTS.md for now)
- <topic> — could suit a <global | project-local> skill; <one-line reason>

**Contradictions**
- <each contradiction + chosen resolution + "confirm?" if interactive>

**Verification commands discovered**
- <commands found in Makefile/justfile/etc.>
```

**Always wait for explicit confirmation before applying — even in yolo / auto-approve mode.** AGENTS.md refactors restructure how every future session in this repo loads context; the blast radius (every later agent invocation) is too high for "announce and proceed". Print the plan, ask once, then wait.

## 5. Apply

After the plan is accepted (or auto-proceeded in yolo):

1. **Stash any uncommitted changes to the agent files** so the refactor diff is recoverable: if `git status` shows the target files as modified, `git stash push -m "reagents: pre-refactor"` them (or just commit current state, depending on repo convention). Note this in the output.
2. **Write the new root file in place.** Don't create `AGENTS.refactored.md` — that creates a duplicate-source-of-truth problem.
3. **Create subdirectory files** at proposed paths.
4. **Don't auto-create skill files.** Skill candidates identified in step 3 stay in AGENTS.md for now; list them in the report so the user can run `/document-skills:skill-creator` on each one when ready. The skill-creator handles trigger descriptions, scope choice, and content reframing — those are design calls that don't belong inside a refactor.
5. **Report**: paths created / modified / deleted, root line count delta, anything that needs human follow-up (resolved contradictions, flagged skill candidates).

## Root file target shape

```markdown
# <Project Name>

<One-sentence description.>

## Where things live

- `path/` — one-line description
- ...

## Commands

<per-service if multi-service, otherwise just the essentials>

## Gotchas

- <project-specific footgun>

## Verification

After changes, run: `<test cmd>`, `<lint cmd>`, `<typecheck cmd>`

## Subdirectory configs

- [`service-a/AGENTS.md`](service-a/AGENTS.md) — local conventions for service A
```

Aim for the root under 100 lines. Per-service files can grow as needed — they only load when Claude is working in that area.

## Keep / Move / Remove cheat sheet

| Keep in root | Move to subdirectory `AGENTS.md` | Flag as skill candidate | Remove |
|---|---|---|---|
| Directory map | Conventions scoped to one service | Multi-step workflows (>20 lines) | Generic advice |
| Cross-cutting commands | Per-service test/lint commands | Reusable domain how-tos | Language/framework basics |
| Project-wide gotchas | Service-specific deployment notes | Procedures used in 2+ projects | Type defs duplicated from code |
| Domain glossary | Local architecture patterns | (flagged only — extract via skill-creator) | Stale model-compensation rules |
| Pointers to subdir configs |  |  | Personal prefs (belong in `~/.agents/AGENTS.md`) |

## Adjacent improvements to mention (don't apply silently)

While diagnosing, note these for the user but don't change them as part of the refactor:

- Missing `.claudeignore` / `permissions.deny` rules — per Anthropic, version-controlled noise reduction *"so every developer on the team gets the same noise reduction"*.
- LSP server not configured — *"symbol-level precision: it can follow a function call to its definition, trace references"* — only worth flagging if the language has good LSP support and the repo is big enough to benefit.
- Multiple agent-config files out of sync (e.g., `AGENTS.md` and `.github/copilot-instructions.md` disagree). Suggest consolidation via symlink.
- Stale agent-config copies inside `.worktrees/`, old branches, or `node_modules/` mirrors. These confuse `grep` and AI search; flag for cleanup but don't touch them as part of this refactor.
- `.claude/settings.local.json`, `.mcp.json`, or other agent-runtime config that interacts with the agent-config files (e.g., MCP servers the AGENTS.md doesn't mention). Worth flagging since the user may want them cross-referenced.
