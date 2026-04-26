---
name: deps-upgrade-report
description: Generate a dependency upgrade report for outdated packages and pinned GitHub Actions. Detects the project's dependency surfaces (uv/Python, npm/Node, and `.github/workflows/` action pins) and runs one agent per detected surface in parallel — each gathers outdated entries, fetches changelogs/release notes, assesses breaking changes against the codebase, and writes a skimmable markdown report. Use when the user asks to "check for outdated dependencies", "dependency upgrade report", "what needs updating", "review dependency updates", "update github actions", "outdated workflows", "monthly dependency audit", or any variation of checking/reporting on outdated packages or actions. Covers Python (uv), Node (npm), and GitHub Actions only.
---

# Dependency Upgrade Report

Generate skimmable markdown reports for outdated direct dependencies and pinned GitHub Actions. The slow step is release-note research — one agent per detected surface runs **in parallel** so a project that uses all three doesn't serialize.

## Architecture

```
detect-managers.sh
        │
        ├──▶ Agent: Python   ──▶ tmp/DEPS_UPGRADE_REPORT_PYTHON.md
        │      (gather → filter → research → assess → write)
        │
        ├──▶ Agent: Node     ──▶ tmp/DEPS_UPGRADE_REPORT_NODE.md
        │      (gather → filter → research → assess → write)
        │
        └──▶ Agent: Actions  ──▶ tmp/DEPS_UPGRADE_REPORT_ACTIONS.md
               (gather → dedupe → research → assess → write)
                        ▲
                        │
                concurrent — single message, multiple Agent calls
```

## Workflow

### Step 1: Detect dependency surfaces

Run from the project root:

```bash
<skill_dir>/scripts/detect-managers.sh
```

Output is JSON: `{"python":true,"node":false,"actions":true}`. A surface counts as detected only when **both** its config and its required CLI are present:

- **python**: `pyproject.toml` exists AND `uv` is on PATH
- **node**: `package.json` exists AND `npm` is on PATH
- **actions**: `.github/workflows/` exists with at least one `.yml`/`.yaml` AND `gh` is on PATH

If none are detected, tell the user and stop. The fan-out scales to whatever subset is detected — one, two, or three agents.

`<skill_dir>` is the absolute path to this skill's directory — capture it now (e.g. via `realpath` of the SKILL.md path) so it can be passed into agent prompts.

### Step 2: Spawn one agent per detected surface — in parallel

**Critical:** issue all Agent tool calls in a **single message** with multiple tool-use blocks so they execute concurrently. Issuing them sequentially defeats the whole point of this skill.

Use `subagent_type: general-purpose` for each. Spawned agents inherit no context from this conversation, so each prompt must be fully self-contained — pass absolute paths, not relative ones.

**Prompt template (substitute `<surface>` with `Python` | `Node` | `Actions`, lowercase the workflow filename, and uppercase the report filename):**

> You are running the **<surface>** half of the deps-upgrade-report skill.
>
> Project root: `<absolute project path>`
> Skill directory: `<skill_dir>`
>
> Read and follow `<skill_dir>/references/<surface-lower>-workflow.md` exactly. It contains the full procedure: gather outdated entries, research release notes (preferring `gh release view` for GitHub-hosted projects), assess breaking-change risk against the codebase/workflows, and write `tmp/DEPS_UPGRADE_REPORT_<SURFACE-UPPER>.md` using the format in `<skill_dir>/references/report-template.md`.
>
> When done, return a one-paragraph summary: counts per group, number of breaking changes flagged, the absolute path to the report (or "no upgrades needed"), and any `tmp/` gitignore warning.

### Step 3: Aggregate

When all spawned agents return, write a brief top-level summary for the user listing each report file, the per-group outdated counts, and whether breaking changes were flagged. Surface any `tmp/` gitignore warnings.

If an agent reported "no upgrades needed", reflect that — don't pretend a missing file is an error.

## Bundled resources

### Reference files
- **`references/python-workflow.md`** — Full procedure for the Python/uv agent
- **`references/node-workflow.md`** — Full procedure for the Node/npm agent
- **`references/actions-workflow.md`** — Full procedure for the GitHub Actions agent
- **`references/report-template.md`** — Output format all agents must match

### Scripts
- **`scripts/detect-managers.sh`** — Emits JSON of detected surfaces
- **`scripts/list-direct-deps-python.py`** — Extracts direct deps from `pyproject.toml`, grouped by `main` / `optional:*` / dependency-group name
- **`scripts/list-direct-deps-node.sh`** — Extracts direct deps from `package.json`, grouped by `dependencies` / `devDependencies` / `peerDependencies` / `optionalDependencies`
- **`scripts/list-direct-actions.py`** — Extracts third-party `owner/repo@ref` pins from `.github/workflows/*.y*ml`, grouped by workflow file

The scripts are deterministic — invoke them rather than re-deriving their logic in the agent.
