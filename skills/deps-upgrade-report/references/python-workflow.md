# Python (uv) Workflow

Procedure for the Python agent spawned by the deps-upgrade-report skill. Run from the project root.

## 1. Gather outdated dependencies

```bash
uv tree --outdated --all-groups --depth 1
```

`--depth 1` restricts output to direct dependencies, which is all this report covers. `--all-groups` includes PEP 735 `[dependency-groups]`.

`uv tree` exits 0 even when packages are outdated. If the command itself errors, stop and surface the error rather than producing a partial report.

## 2. Filter to direct dependencies

Run the helper:

```bash
<skill_dir>/scripts/list-direct-deps-python.py
```

It prints JSON like:

```json
{
  "main": ["httpx", "pydantic"],
  "optional:test": ["pytest"],
  "dev": ["mypy", "ruff"],
  "build-system": ["uv_build", "hatchling"]
}
```

Group keys:
- `main` — `[project.dependencies]`
- `optional:<name>` — `[project.optional-dependencies.<name>]`
- `<name>` — PEP 735 `[dependency-groups.<name>]`
- `build-system` — `[build-system].requires` — handled separately in step 2b below, since `uv tree --outdated` does **not** see these (build backends aren't in the project venv)

Intersect the runtime groups (everything except `build-system`) with the outdated list from step 1 (names from both sides are PEP 503 normalized). Discard anything not in the direct-dep map — those are transitive.

## 2b. Check build-system pin freshness

The `build-system` group needs a separate freshness check because `uv tree` ignores it. For each entry in that group:

1. Find the pin spec from `[build-system].requires` — usually a constraint like `uv_build>=0.4.15,<0.5.0` or an exact pin like `hatchling==1.27.0`.
2. Look up the latest release on PyPI:
   ```bash
   curl -s https://pypi.org/pypi/<name>/json | jq -r '.info.version'
   ```
3. Decide whether to flag as outdated:
   - **Pin caps below latest** (`<0.5.0` but latest is `0.6.0`): outdated — the constraint blocks the user from receiving the new version on next build. Treat as a soft Hold and recommend bumping the constraint.
   - **Exact pin below latest** (`==1.27.0` but latest is `1.30.0`): outdated — recommend bumping the pin.
   - **Pin allows latest** (`>=0.4.15` with no upper, or `>=1.0,<2.0` with latest still in range): the next clean build picks up the latest automatically — skip.

Build-system entries do **not** have load-bearing usage in project source (they only run during wheel-build), so the breaking-change risk assessment in step 4 reduces to "did the build backend change CLI args, config-key syntax, or supported Python versions?" Cite `pyproject.toml` lines that pass any deprecated configuration.

Always check the changelog for security-advisory markers (CVE, GHSA) — build-backend security alerts are exactly the kind of thing dependabot catches that this report should also surface.

## 3. Research changelogs

For each outdated direct dependency, find release notes between the current and latest version.

**Preferred order:**

1. Look up the project's repository URL in `[project.urls]` of `pyproject.toml`. If absent, query PyPI: `curl -s https://pypi.org/pypi/<name>/json | jq '.info.project_urls'`.
2. If GitHub-hosted, prefer `gh` over web scraping:
   - `gh release list -R <owner>/<repo> --limit 30`
   - `gh release view <tag> -R <owner>/<repo>` for each tag between current and latest
3. Otherwise web search: `<package> changelog` or `<package> release notes`.
4. If no changelog can be located, mark "Changelog not found" with a link to `https://pypi.org/project/<name>/`.

Extract entries strictly between current and latest. Summarise concisely while preserving enough detail to skim without clicking through.

## 4. Assess breaking-change risk

Scan changelog excerpts for:
- Major version bumps (semver) — assume potentially breaking
- **0.x packages: any minor bump is potentially breaking** (semver does not protect 0.x)
- Calver packages: rely on explicit changelog markers, not version arithmetic
- Sections marked "BREAKING", "Breaking Changes", "Migration", "Removed", "Deprecated"
- API signature changes, dropped Python version support

For each breaking change, grep the project source for usage of the affected symbol/API. State whether the project actually touches it and cite specific files (`src/foo/bar.py:42`).

## 4b. Detect deliberate version caps (Holds)

Re-read `pyproject.toml` and find explicit upper-bound constraints on direct deps — e.g. `posthog<6`, `dj-stripe>=2.0,<2.9.2`, `numpy~=1.26`. Any cap that excludes the latest release is a deliberate **Hold** by the project owner, usually pinned because newer versions break load-bearing code.

For each cap that excludes the latest available version:

1. Use the step 3 changelog to identify what was removed/rewritten in the version range above the cap.
2. Grep the project for usage of those removed APIs/modules. Cite the specific files and line numbers that depend on the capped behavior.
3. In the report, surface the entry inside the **Breaking Changes & Warnings** section with:
   - **Risk to this project:** `Hold — high.` followed by the citation.
   - **Recommended action:** `Do not bump.` followed by the reason (e.g. *"v6 removes `posthog.identify()` used at `pdj/core/middleware.py:164`"*). Add a one-line migration sketch only if a clean path is obvious.

If a cap exists but no codebase usage of the would-be-broken APIs is found, surface it as **Hold — review**: the cap may be vestigial and worth retesting.

## 5. Write the report

Write `tmp/DEPS_UPGRADE_REPORT_PYTHON.md` using the format in `<skill_dir>/references/report-template.md`.

- **Emit the Summary table first** — one row per outdated direct dep, sorted breaking-first then alphabetical (`Yes` rows, then `Hold` rows, then `No` rows; alphabetical within each band). Columns: Package, Current → Latest, Breaking? (`Yes`/`No`/`Hold`), Group (`main`/`dev`/`test`/`optional:*`/`build-system`), Changelog (direct link). For `build-system` rows, show the pin spec on the left of the arrow (e.g. `>=0.4.15,<0.5.0`) and the latest available on the right.
- Then the **Breaking Changes & Warnings** section (Holds and breaking entries together, with code citations).
- Then **per-group detail sections** with full changelog excerpts.
- Use `<details>` blocks for changelog excerpts longer than ~30 lines.
- Always include clickable links to changelogs — the Summary table link and the per-group section link should point to the same canonical URL.

Create `tmp/` if it does not exist. Verify it is gitignored (`grep -qx 'tmp/\?' .gitignore 2>/dev/null`); if not, warn in the return summary so the user can add it before committing.

If no outdated direct deps are found, do **not** write the report. Return the single-line "no upgrades needed" summary instead.

## Return value

Return one paragraph summarising:
- Counts per group (e.g., "main: 4 outdated, dev: 2 outdated")
- Number of breaking changes flagged
- Absolute path to the report file (or "no upgrades needed")
- Any `tmp/` gitignore warning
