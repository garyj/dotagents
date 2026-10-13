---
name: apm-skills
description: Install and manage agent skills, APM packages, and MCP servers with APM (Agent Package Manager, microsoft/apm CLI). Use when asked to install, add, update, remove, or audit a skill, package, or MCP server in a project or globally, or when editing apm.yml or apm.lock.yaml.
---

# Managing skills and MCP servers with APM

APM (microsoft/apm) manages agent skills, packages, and MCP servers for several harnesses from one `apm.yml`,
deploying to each harness's own config layout. `apm --help` and the per-command reference behind
https://microsoft.github.io/apm/llms.txt (llms-small, llms-full, and consumer, producer, and enterprise ramps) are
current; APM moves fast, so fetch the relevant ramp instead of relying on training data.

## Traps

- Depend on the plugin subpath (`apm install sveltejs/ai-tools/plugins/claude/svelte`), never the repo root: the
  root vendors the whole monorepo, deploys nothing, and can drag in broken dev-only MCP servers.
- The claude target resolves `${VAR}` placeholders in MCP headers and env at install time and writes the literal
  value into `.mcp.json`; copilot and kiro substitute at runtime. A shell that auto-loads `.env` makes the leak
  automatic. Keep real keys out of `apm.yml`; prefer OAuth remote HTTP servers.
- `apm audit --file <path>` takes one path per call, so loop it over many files; this repo's prek hook does exactly
  that. `--strip` removes the characters. `apm audit --ci` runs the lockfile and policy checks.
- The PyPI packages `apm` and `apm-cli` are unrelated projects. APM ships as GitHub release tarballs.
- When the binary comes from a version manager (mise and the like), don't use `apm self-update`; it fights the
  manager.
- Packages that ship `lifecycle:` scripts run them only after `apm lifecycle trust` in that project.

## Where files land

- Package source of truth: `apm_modules/<owner>/<pkg>/`, gitignored.
- Skills: shared `.agents/skills/<name>/` plus per-harness copies for the active targets. Hooks: scripts under
  `.claude/hooks/<pkg>/`, registrations merged into `.claude/settings.json`.
- Commit `apm.yml` and `apm.lock.yaml`. Never hand-edit APM-deployed files; change `apm.yml` and re-run
  `apm install`.
