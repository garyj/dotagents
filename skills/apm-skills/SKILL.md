---
name: apm-skills
description: Install and manage agent skills, APM packages, and MCP servers with APM (Agent Package Manager, microsoft/apm CLI). Use when asked to install, add, update, remove, or audit a skill, package, or MCP server in a project or globally, or when editing apm.yml or apm.lock.yaml.
---

# Managing skills and MCP servers with APM

APM (microsoft/apm) manages agent skills, packages, and MCP servers for multiple harnesses from a single `apm.yml`
manifest, deploying to each harness's own config layout.

## Install packages / skills

- Into the current project: `apm install <owner>/<repo>` (GitHub shorthand). Monorepo subpaths work:
  `apm install sveltejs/ai-tools/plugins/claude/svelte`.
- Depend on the plugin subpath, never the repo root: the root vendors the whole monorepo, deploys nothing, and can
  drag in broken dev-only MCP servers.
- Bare `SKILL.md` packages and `plugin.json` collections install the same way. `--skill NAME` (repeatable) pins a
  subset of a multi-skill bundle.
- Everything from the manifest: plain `apm install` (reads `apm.yml`, auto-created if missing). `--frozen` refuses to
  run when the lockfile is missing or out of sync (CI-safe).
- User scope instead of project: `apm install -g` (lands in `~/.apm/`).
- Choose harnesses: `-t claude`, comma-separated `-t claude,copilot`. Resolution: `--target` > `apm.yml targets:` >
  `apm config` > auto-detect.
- Preview with `--dry-run`; dev-only dependency with `--dev`.

## MCP servers

- Discover: `apm mcp search <query>`, `apm mcp show <name>`, `apm mcp list` (registry defaults to
  https://api.mcp.github.com).
- From the registry: `apm mcp install <name>` (alias for `apm install --mcp <name>`); pin with `--mcp-version`.
- Self-defined remote: `apm install --mcp <name> --transport http --url https://... [--header KEY=VALUE]`.
  Self-defined stdio: `apm install --mcp <name> -- npx -y <pkg>`, env via `--env KEY=VALUE`.
- Entries live in `apm.yml` under `dependencies.mcp`; deployed per active target to `.mcp.json`, `.vscode/mcp.json`,
  `.codex/config.toml`, etc. Out-of-target runtimes are skipped with an `[i]` line.
- Secret trap: the claude target resolves `${VAR}` placeholders in headers/env at install time and writes the literal
  value into `.mcp.json` (copilot/kiro substitute at runtime instead). Shells that auto-load `.env` (direnv etc.)
  make the leak automatic. Keep real keys out of `apm.yml`; prefer OAuth remote HTTP servers.

## Where files land (project scope)

- Package source of truth: `apm_modules/<owner>/<pkg>/` (gitignored).
- Skills: shared `.agents/skills/<skill-name>/` plus per-harness copies (e.g. `.claude/skills/`) for the active
  targets. `--legacy-skill-paths` restores the old per-client layout.
- Hooks: scripts under `.claude/hooks/<pkg>/`, registrations merged into `.claude/settings.json`.
- Manifest and lock: `apm.yml`, `apm.lock.yaml`. Commit both.
- Never hand-edit APM-deployed files; change `apm.yml` and re-run `apm install`.

## Update / remove / audit

- `apm outdated` shows drift; `apm update` renders an interactive plan; `apm update --yes` in automation.
- `apm uninstall <owner>/<repo>` removes the package, its deployed files, and the `apm.yml` entry.
- `apm audit --file <path>` scans one file for hidden Unicode; it takes a single path per call, so loop it for many
  files. `--strip` removes the characters. `apm audit --ci` runs the lockfile/policy consistency checks, suited to
  CI and pre-push gates.
- Packages shipping `lifecycle:` scripts run them only after `apm lifecycle trust` in that project (state in
  `~/.apm/scripts-trust.json`).

## Authoring packages

- `apm init` scaffolds `apm.yml`; with `includes: auto` the package ships local content from `.apm/`
  (`skills/`, `prompts/`, `instructions/`, `agents/`, `hooks/`, `commands/`). `apm plugin init` and
  `apm marketplace init` scaffold those shapes.
- MCP servers a package provides are its own `dependencies.mcp` entries; consumers inherit them transitively
  (self-defined ones require re-declaration or `--trust-transitive-mcp` on the consumer side).
- Producer ladder: author primitives, then `apm compile`, check with `apm preview` / `apm view`, `apm pack` a
  distributable, `apm publish` to a registry or marketplace. Consumers install with `apm install <owner>/<repo>`.
- Before starting authoring work, fetch the producer ramp doc below; it is the authoritative, current reference.

## Docs

- Site: https://microsoft.github.io/apm/ with LLM-ready indexes at https://microsoft.github.io/apm/llms.txt
  (llms-small/llms-full variants plus per-audience ramps: consumer, producer, enterprise, and a per-command CLI
  reference under `_llms-txt/`). Fetch the relevant ramp instead of relying on training data; APM moves fast.

## Gotchas

- The PyPI packages named `apm` and `apm-cli` are unrelated projects; APM ships as GitHub release tarballs. Never
  install it from PyPI.
- When the binary comes from a version manager (mise etc.), don't use `apm self-update`; it fights the manager.

## Appendix: version notes

- apm <= 0.26.0 rewrites `generated_at` in `apm.lock.yaml` on every `apm install`/`apm lock` even when nothing
  changed, which intermittently trips lockfile-in-sync git hooks. Fixed in v0.27.0 (microsoft/apm#2306).
