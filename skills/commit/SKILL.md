---
name: commit
description: Create well-formatted commits that match the current repo's existing convention. Use when committing code changes, staging files, or creating atomic git commits. Detects the repo's prefix vocabulary, subject style, and body style from history instead of imposing one format.
---

# Smart Git Commit

Create a well-formatted commit: $ARGUMENTS

## Current Repository State

- Git status: !`git status --porcelain`
- Current branch: !`git branch --show-current`
- Staged changes: !`git diff --cached --stat`
- Unstaged changes: !`git diff --stat`
- Recent commits (subjects only): !`git log --pretty=format:'%s' -30`
- Recent commits with bodies: !`git log --pretty=format:'%H%n%s%n%b%n---' -5`

**Note**: If the branch name contains a Jira (e.g., `ABC-123`) or GitHub issue (e.g., `GH-456`), include it in the commit message **only if** the repo's history shows that pattern.

## Step 1 — Detect the Repo's Convention (do this first)

Before writing anything, analyze the `git log --pretty=format:'%s' -30` output above and infer:

1. **Prefix vocabulary.** What verbs/types does this repo use?
   - Conventional commits → `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`, `build:`, `ci:`, `perf:`, `style:`
   - Chezmoi/dotfiles style → `add:`, `update:`, `fix:`, `cut:`
   - Imperative, no prefix → `Add X`, `Fix Y`, `Refactor Z`
   - Gitmoji → `:sparkles: add X`, `:bug: fix Y`
   - Ticket-prefixed → `[ABC-123] …`
   - None / ad-hoc → no consistent pattern
2. **Scope syntax.** Does the repo use `type(scope): …` (e.g., `update(debian):`, `fix(auth):`)? If so, what scopes appear?
3. **Subject style.**
   - Case: lowercase first word, Sentence case, or Title Case?
   - Ending: trailing period or not?
   - Length: typically under 50 chars, under 72, or longer?
   - Structure: starts with a verb (`add`), a noun (`bringme keybindings`), or a sentence?
4. **Body style.**
   - Always, sometimes, or never present?
   - Wrapped at ~72 columns?
   - Bullet points, prose, or both?
   - Explains **why** vs. **what**?
5. **Footers.** Does history include `Co-Authored-By:`, `Signed-off-by:`, `Refs:`, `Closes #…`? Do **not** add footers the repo doesn't already use.

**Match what you find.** Do not impose conventional commits on a repo that doesn't use them. Do not add `feat:` to a repo that writes `add:`. Do not add a body to a repo whose subjects stand alone.

If the repo has **no consistent pattern**, default to Conventional Commits (see reference below) and keep the subject under 72 chars.

## Step 2 — Commit Workflow

1. Unless `--no-verify` is passed, respect the repo's pre-commit hooks.
2. Extract any Jira/GH issue from the branch name **only if** the repo's history shows issue references.
3. Check staged files with `git status`.
4. If 0 files are staged, stage modified and new files — prefer naming files explicitly over `git add -A` when sensitive files (`.env`, credentials) could be in the tree.
5. Review the diff to understand the change.
6. Decide if the diff represents **one logical change** or several. If several (unrelated concerns, mixed types, different directories), offer to split into atomic commits. For small repos (dotfiles, configs, single-purpose tools) a single commit is usually correct.
7. Write the commit message in the detected style.
8. Review the staged diff against the message — does the subject accurately describe what changed?

## Known Convention Patterns (reference)

Use these as templates once Step 1 has identified which one applies. Do **not** pick one arbitrarily.

### Pattern A — Conventional Commits

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, `infra`, `dev`.

Two non-standard types worth calling out explicitly (used often in this user's DevOps / dev-environment work):

- **infra** — deployment infrastructure changes: AWS/GCP/Render/DO resources, Terraform, CDK, Kubernetes manifests, CI runners, DNS, secrets management. Example: `infra: add Redis caching to AWS CDK`.
- **dev** — developer-experience changes: tooling updates, local dev environment tweaks, editor/IDE config, shell/workflow improvements, internal scripts that only run on developer machines. Example: `dev: add Claude command for better testing`.

Example: `feat(auth): add password strength validation`

### Pattern B — Chezmoi / Dotfiles Verbs

```
<verb>(<optional scope>): <lowercase description, no period>
```

Verbs:

- **add** — new config, new tool, new script, new alias, new keybinding
- **update** — modify existing config, change settings, tweak behavior
- **fix** — correct something broken
- **cut** — remove config, disable a tool, delete a script or alias

Common scopes: `(debian)`, `(ghostty)`, `(atuin)`, `(ssh)`, `(git)`. Omit scope when the change is general.

Examples from real history:

```
add: mongodb-tools installer (mongodb-org-tools + mongodb-atlas)
update: starship directory styling for repo roots
fix: make Super+slash reliably bring Chromium to workspace
cut: remove TODO-snap-migration.md
update(debian): bringme.sh and move-to-workspace.sh to use window-tools D-Bus extension
fix(debian): use chezmoi.homeDir template for GNOME shortcut paths
```

Bodies are used when the **why** is non-obvious — e.g., explaining a workaround, a root cause, or a migration step. Keep the subject under 72 chars and wrap the body at ~72.

### Pattern C — Plain Imperative

```
Add X to Y
Fix race condition in foo()
Refactor parser into three passes
```

Title Case or sentence case, no prefix, no period. Common in Linux kernel, older Git history, many Go projects.

### Pattern D — Ad-hoc

No detectable pattern. Fall back to Conventional Commits (Pattern A).

## Subject-Line Rules (apply to all patterns)

- Focus on **what changed** in a way that helps a reader skimming `git log --oneline`.
- Be specific: `fix: resolve memory leak in render loop` beats `fix: bug`.
- Prefer the imperative mood when the detected pattern allows it (`add X`, not `added X` or `adds X`).
- Don't restate the file name unless it's the clearest framing.
- Never include `Claude`, `AI`, or tool names unless the change is literally about those tools.

## Body Rules

- Only add a body if the repo's history shows bodies **and** the change needs explanation.
- Explain **why**, not **what** — the diff shows the what.
- Wrap at ~72 columns.
- Bullet points are fine when the change has multiple discrete parts.

## Footer Rules

- Match the repo. If `git log` shows `Co-Authored-By:` or `Signed-off-by:`, include them. If not, don't add them.
- For AI attribution specifically: only add a `Co-Authored-By: Claude …` line if the repo's existing history already includes similar attribution. Many repos (including most dotfiles) explicitly do not.

## Splitting Commits

Split when the diff mixes:

1. **Different concerns** — unrelated parts of the codebase
2. **Different change types** — e.g., a feature + a refactor + a doc update
3. **Different file categories** — source vs. generated vs. config
4. **Reviewability** — one reviewer shouldn't have to hold three contexts at once

Do **not** split when:

- The change is a single logical unit across several files (common in dotfiles, refactors, schema migrations)
- Splitting would produce commits that don't build / pass tests on their own

## Command Options

- `--no-verify`: Skip pre-commit hooks (use sparingly; investigate failures first)
- `--amend`: Amend the previous commit instead of creating a new one (only when the previous commit hasn't been pushed or the user explicitly asks)

## Important Notes

- **Never commit without explicit user approval** unless the user has already said "commit" in this turn. Showing `git diff --staged` and waiting is the default.
- Review the staged diff against the proposed message before committing.
- If pre-commit hooks fail, fix the underlying issue rather than bypassing with `--no-verify`.
- Never force-push, reset hard, or amend published commits without explicit confirmation.
