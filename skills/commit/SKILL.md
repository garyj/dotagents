---
name: commit
description: Create git commits that mirror the repo's existing convention. Falls back to Conventional Commits (with `infra` and `dev` types) when no pattern is detectable. Use when committing code, staging files, or creating atomic commits.
---

Create a git commit (or several) for the current changes. Mirror the repo's existing style from `git log`. Fall back to Conventional Commits only when no pattern is detectable.

## Mirror the repo

Check `git log --pretty=format:'%s' -30` first. Match what you find:

- **Prefix vocabulary** — e.g., `feat:`/`fix:` (Conventional), `add:`/`update:`/`fix:`/`cut:` (chezmoi/dotfiles), `Add X`/`Fix Y` (plain imperative), or none.
- **Scope syntax** — does the repo use `type(scope): …`? Which scopes appear?
- **Subject style** — case, trailing period or not, length, verb-first vs. noun-first.
- **Body style** — always / sometimes / never; bullets vs. prose; *why* vs. *what*.
- **Footers** — only include `Co-Authored-By:`, `Signed-off-by:`, `Refs:` etc. if history already does. Never add `Co-Authored-By: Claude` unless prior commits already do.

Do not impose Conventional Commits on a repo that doesn't use them.

## Fallback (when no pattern is detectable)

```
<type>(<optional scope>): <description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, `infra`, `dev`.

- **infra** — deployment infra: AWS/GCP/Render, Terraform, CDK, Kubernetes, CI runners, DNS, secrets.
- **dev** — developer experience: tooling, local env, editor/IDE, shell/workflow, dev-only scripts.

Subject: lowercase after the colon, no trailing period, ≤72 chars, imperative mood.

## Issue references

Only include issue references if the repo's history already uses them (check `git log`) or the user explicitly asks. Detect the issue from the branch name (e.g., `fix/ABC-123-foo`, `gh-456-thing`) or from arguments.

Place the reference at the **end of the subject line** (not the body), inside parentheses if it reads more naturally that way. Keep the subject under 72 chars.

**GitHub** — closing keywords auto-close the linked issue when the commit lands on the default branch or the PR merges:

- `fix: resolve login redirect loop (closes #123)`
- `fix: resolve login redirect loop, fixes #123`
- Cross-repo: `closes owner/repo#123`
- Reference only (no close): `(refs #123)`

**Jira Smart Commits** — append the issue key plus optional commands at the end of the subject:

- `fix login redirect loop ABC-123`
- `fix login redirect loop ABC-123 #close`
- `fix login redirect loop ABC-123 #time 1h #close`

Commands: `#comment <text>`, `#time 2h <description>`, `#close` / `#done` / `#resolve`.

## Splitting commits

Split when the diff mixes:

1. Unrelated parts of the codebase
2. Different change types (feature + refactor + docs)
3. Source vs. generated vs. config
4. Things a reviewer shouldn't have to hold all at once

Do NOT split when the change is one logical unit across several files, or when splitting would produce commits that don't build / pass on their own.

## When to proceed vs. ask

Explicit invocation (e.g., `/commit`) IS the approval. Default to action.

**Proceed silently when:**
- The diff is one logical change OR has an obvious split boundary, AND
- The convention is clear from `git log` (or the fallback applies), AND
- The message accurately describes the diff.

**Stop and ask when:**
- The diff has multiple reasonable ways to split.
- Sensitive files (`.env`, credentials, large binaries) are staged or about to be staged.
- About to touch published history (amend, rebase, force-push).
- The repo style requires a body and the *why* is genuinely unclear.

## Steps

1. Treat caller-provided arguments as additional guidance. File paths/globs limit which files to commit; freeform text influences scope, summary, and body.
2. Check `git status` and `git diff` to understand the changes.
3. Check `git log --pretty=format:'%s' -30` to detect the convention.
4. Decide how many commits to create (see [Splitting commits](#splitting-commits)).
5. Stage only the intended files. Prefer naming files explicitly over `git add -A` when sensitive files could be in the tree.
6. Commit with the detected style (or fallback). Only commit; do not push.
7. Respect pre-commit hooks. If they fail, fix the underlying issue rather than using `--no-verify`.
