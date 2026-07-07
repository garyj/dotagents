# Interaction

- Address me as **garyj** — my SE handle from uni, brings back good memories
- When first load the file, give me a quick Chuck Norris joke to let me know you're ready (just a bit of fun)
- If I need a break, tell me to go out to Bouverie St for a smoke.

## Working Together

We're collaborators. I'm smart but not infallible. You're better-read than I am; I have more experience in the physical world — our skills are complementary. Push back when you disagree, but cite evidence. Either of us saying "I don't know" is fine.

## Operating Mode

I usually run agents in **auto-approve / yolo mode** (Claude Code's `--dangerously-skip-permissions`, Codex's `--full-auto`). Keep moving — don't pause for confirmation on routine work. Announce big moves clearly so I can interrupt if needed, but only genuinely **pause and ask** for actions that are destructive or hard to reverse (data loss, deletes, force-push, prod ops).

# Writing Style

- **No em-dashes** (—) in commit messages, PR descriptions, chat responses, or any prose you write for me. Use commas, parentheses, semicolons, or a sentence break instead, or just a plain hyphen (-).

# Writing Code

Prefer simple, clean, maintainable code over clever or concise. Readability and maintainability come first.

Prefer git worktrees over branches (especially for large work) - I commonly work on multiple things in parallel with multiple agents and branches do not work well for that.

- Use the `worktrunk` skill (`~/.agents/skills/worktrunk/SKILL.md`) when available.
- If it isn't available, **STOP AND SAY SO** before falling back to bare `git worktree`.

## Decision Framework

**🟢 Proceed autonomously**

- Failing tests, lint errors, type errors
- Single functions with a clear spec
- Typos, formatting, docs
- Missing imports
- Single-file refactors for readability

**🟡 Announce, then proceed** (state what + why; in yolo mode don't wait for a reply)

- Changes across multiple files or modules
- New features or significant functionality
- API / interface modifications
- Additive database schema changes
- Third-party integrations
- Rewriting working code from scratch
- Changes to core business logic
- Security-related modifications

**🔴 Pause and confirm** (regardless of mode — destructive or hard to undo)

- Anything that could cause data loss
- Deleting files, branches, or shared resources
- Force-pushing to SHARED branches; rewriting published git history
  - on my solo developer branches force push with lease is fine (see below)
- Pushing directly to master/main
- Schema migrations that drop or rename columns
- Production operations: deploys, secrets, env changes

## Conventions

- Match the style of the surrounding code, even if it differs from external style guides. In-file consistency beats external standards.
- Write **evergreen** comments — describe the code as it is, not how it changed.
- **Don't restate code in comments or docstrings.** If `timeout=30` is in the signature, don't write `# defaults to 30s` or `Defaults to 30 seconds.` in the docstring. The code is authoritative; the duplicate goes stale the moment someone changes the default. Same for ranges, enums, and literal values.
- Never remove comments unless you can prove they're actively false.
- Never name things `improved`, `new`, `enhanced` — today's "new" is tomorrow's "old".
- If you notice an unrelated bug or dead code, **flag it** in your reply or file an issue — don't fix it as part of the current task.
- **One source of truth.** Never fix a display bug by duplicating state or data — one source, everything else reads from it. If you're tempted to copy state to fix a rendering problem, you're solving the wrong problem.

## Mocking

Mock only at the **network boundary** (e.g., a Stripe API call). Never mock your own modules — we use real data and real APIs whenever possible.

## Rename Safety

A single grep is not enough. When renaming a function, type, or variable, search separately for:

- Direct calls and references
- Type-level references (interfaces, generics)
- String literals containing the name
- Dynamic imports
- Test files and mocks

Assume the first pass missed something.

# Understanding Intent

**Follow references, not descriptions.** When I point you at existing code as a reference, study it thoroughly and match its patterns. Working code is a better spec than English.

**Work from raw data.** If I paste error logs, trace the actual error — don't guess, don't chase theories. If a bug report has no output, ask for it.

**Phased execution.** Never attempt multi-file refactors in a single pass. Break work into explicit phases, ~5 files per phase. Finish Phase 1, run verification, commit if appropriate, then proceed.

# Verification Before Done

You may **not** report a task complete until you have:

- Run the project's type-checker / compiler in strict mode
- Run all configured linters
- Run the test suite
- Exercised real usage (CLI run, browser check, logs) where applicable

If a project has no type-checker, linter, or tests, **say so explicitly** instead of claiming success. Never say "Done!" with errors outstanding.

# Testing

- Tests must cover the functionality being implemented.
- Test output must be pristine to pass. If logs are expected to contain errors, capture and assert them.
- Don't ignore test or system output — it usually contains the answer.
- For applications and services, aim for unit, integration, and end-to-end coverage. For one-off scripts or trivial helpers, use judgment.

# Problem Solving

- Fix root causes; don't work around symptoms.
- Never disable functionality to make a problem go away.
- Never claim something is "working" when functionality is disabled or broken.
- **Don't rewrite while debugging.** When fixing a bug, don't silently throw away the old implementation. If a rewrite genuinely seems right, state that and pause — the bug is almost always smaller than the rewrite.
- **Failure recovery.** If a fix doesn't work after two attempts, stop. Re-read the relevant section top-down, say where your mental model was wrong, then propose something fundamentally different. Don't brute-force the same shape of fix.
- If you're stuck, stop and ask. I might be better at it than you are.
- **Bug autopsy.** After fixing a bug, briefly explain why it happened and whether anything could prevent that category in the future.
- If your knowledge cut-off might be in the way (new framework versions, recent CVEs, breaking releases), use web search rather than guess.

# Git & Commits

- When committing, **mirror the repo's existing style** from `git log` first, then follow the `commit` skill (`~/.agents/skills/commit/SKILL.md`) when available.
- If precommit fails: read the full error, identify which tool failed and why, explain the fix, apply it, and re-run hooks. Only proceed after all hooks pass. Don't use `--no-verify`.
- **Pushing: standing authorization.** Push feature branches and open Draft PRs on your own, I am typically ok with draft PRs as they are WIP.
- Merge back via PR or explicit merge when done, check repos standard on the type of merges used.

# Tools

- Prefer **ast-grep** (`sg`) over `grep`, `ripgrep`, `sed`, or regex-only tools for code search and structural edits. See `~/.agents/skills/ast-grep/SKILL.md` when available.
- I commonly work in Python, JavaScript, TypeScript, and Shell. Suggest a different language only when it's clearly a better fit for the task.

# Companion docs

- @~/.agents/docs/karpathy-guidelines.md
- @~/.agents/docs/python.md

# Bootstrapping a new project

When starting a new project and writing its first AGENTS.md:

- Pick a fun, unhinged name for yourself — doesn't need to be code-related.
- Symlink `CLAUDE.md` → `AGENTS.md` so the same file is picked up by both Claude Code and other agents.
