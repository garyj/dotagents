---
name: apm-skills
description: Install agent skills and packages with APM (Agent Package Manager, microsoft/apm CLI). Use when asked to install, add, update, or remove a skill or APM package in a project or globally.
---

# Installing skills with APM

Temporary reference while the apm workflow settles; delete once apm >= 0.24.0 is the daily driver.

## Install

- Into the current project: `apm install <owner>/<repo>` (GitHub shorthand). Monorepo subpaths work: `apm install sveltejs/ai-tools/plugins/claude/svelte`.
- Bare `SKILL.md` packages and `plugin.json` collections install the same way.
- Everything from the manifest: plain `apm install` (reads `apm.yml`, auto-created if missing).
- User scope instead of project: `apm install -g <owner>/<repo>` (lands in `~/.apm/`).
- Choose harnesses: `-t claude`, comma-separated `-t claude,copilot`. Defaults to the `targets:` list in `apm.yml`.
- Preview with `--dry-run`; dev-only dependency with `--dev`.

## Where files land (project scope)

- Package source of truth: `apm_modules/<owner>/<pkg>/`
- Skills: shared `.agents/skills/<skill-name>/` plus per-harness copies (e.g. `.claude/skills/`) for the active targets. `--legacy-skill-paths` restores the old per-client layout.
- Manifest and lock: `apm.yml`, `apm.lock.yaml`. Commit both.

## Update / remove

- `apm update` for an interactive plan; `apm update --yes` in CI.
- `apm uninstall <owner>/<repo>` removes the package and its deployed files.

## Gotchas (v0.23.1, this machine)

- apm is mise-managed (`github:microsoft/apm` in `~/.config/mise/config.toml`). Upgrade via mise; never `uv tool install apm`, it shadows the mise binary.
- Hooks shipped inside packages are broken in v0.23.1 (microsoft/apm#2020 routing, microsoft/apm#2023 runtime); both are fixed upstream and land in v0.24.0. Skills themselves are unaffected.
- `~/dev/pacman/mbs` self-heals its ponytail hooks via a lifecycle script; do not hand-edit its `.claude/settings.json` (see mbs AGENTS.md).
