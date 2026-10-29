---
name: commit
description: Use when the user explicitly says `commit` OR you just need to do a git commit
---

## Mirror the repo

Check `git log --pretty=format:'%s' -30` first and match the repo's style.

## Fallback (when no pattern is detectable)

Use Conventional Commits, with two extra types:

- **infra** — deployment infra: AWS/GCP/Render, Terraform, CDK, Kubernetes, CI runners, DNS, secrets.
- **dev** — developer experience: tooling, local env, editor/IDE, shell/workflow, dev-only scripts.

## Issue references

If the repo's `prepare-commit-msg` hook adds the issue key, don't add it yourself, and leave room for it in the subject. Find the hook with `git rev-parse --git-path hooks/prepare-commit-msg`.

Otherwise, only include issue references if the repo's history already uses them (check `git log`) or the user explicitly asks. Detect the issue from the branch name (e.g., `fix/ABC-123-foo`, `gh-456-thing`) or from arguments.

Place the reference at the **end of the subject line** (not the body), inside parentheses if it reads more naturally that way. Keep the subject under 72 chars.

## Model trailer

Each commit names the model that wrote it. Claude Code adds `Co-Authored-By: <model> <noreply@anthropic.com>` itself. In any other harness, end the message with `Co-Authored-By: <model> <noreply address of the model's vendor>`, using the model name the harness reports. If it reports none, name the harness. Never add a second trailer for the same model.

## Splitting commits

Split when the diff mixes:

1. Unrelated parts of the codebase
2. Different change types (feature + refactor + docs)
3. Source vs. generated vs. config
4. Things a reviewer shouldn't have to hold all at once

Do NOT split when the change is one logical unit across several files, or when splitting would produce commits that don't build / pass on their own.

## When to proceed vs. ask

Explicit invocation (e.g., `/commit`) IS the approval. Default to action.

**Stop and ask when:**
- The diff has multiple reasonable ways to split.
- Sensitive files (`.env`, credentials, large binaries) are staged or about to be staged.
- About to touch published history (amend, rebase, force-push).
- The repo style requires a body and the *why* is genuinely unclear.

## Steps

1. Treat caller-provided arguments as additional guidance. File paths/globs limit which files to commit; freeform text influences scope, summary, and body.
2. Stage only the intended files. Prefer naming files explicitly over `git add -A` when sensitive files could be in the tree.
3. Only commit; do not push.
4. Respect pre-commit hooks. If they fail, fix the underlying issue rather than using `--no-verify`.
