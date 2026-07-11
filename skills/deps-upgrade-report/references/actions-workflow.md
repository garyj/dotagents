# GitHub Actions Workflow

Procedure for the GitHub Actions agent spawned by the deps-upgrade-report skill. Run from the project root.

## 1. Gather and group action references

Run the helper:

```bash
<skill_dir>/scripts/list-direct-actions.py
```

It scans workflow files (`.github/workflows/*.y*ml`), composite/local action definitions (`.github/actions/**/action.y*ml` and a repo-root `action.y*ml`), and any other local action reached via `uses: ./...`. It emits JSON keyed by repo-relative file path, with each entry recording `action`, `ref`, source `line`, and any inline `comment`:

```json
{
  ".github/workflows/ci.yaml": [
    {"action": "actions/checkout", "ref": "v6", "line": 42},
    {"action": "actions/setup-python", "ref": "v6", "line": 51}
  ],
  ".github/workflows/release-deployment.yaml": [
    {"action": "googleapis/release-please-action", "ref": "v4", "line": 18}
  ],
  ".github/actions/setup/action.yml": [
    {"action": "astral-sh/setup-uv", "ref": "v7", "line": 11}
  ]
}
```

Docker actions (`docker://...`) are skipped. Local `uses: ./...` references are followed into their `action.yml` rather than reported as entries — the pins inside them show up under the composite file's own key. Reusable-workflow references (`uses: owner/repo/.github/workflows/x.yml@ref`) are included with `"type": "reusable-workflow"`, `action` set to `owner/repo`, and the workflow path in `"workflow"` — treat them like any other pinned action (research the `owner/repo` releases/tags).

## 2. Deduplicate to a unique action set

Build a unique map of `owner/repo` -> `{refs_seen: set, used_in: [path:line, ...]}`. Multiple files pinning the same action at the same ref are common — research each `owner/repo` once but report the per-file usage (workflows and composite action files alike) so the user knows what they'll be touching.

Classify each ref:

- **Tag** (`v6`, `v6.0.0`) — the common case
- **Branch** (`release/v1`, `main`) — rolling pin; "latest" means newest commit on that branch
- **SHA** (40-hex) — immutable pin; the inline comment usually carries the human tag (e.g. `# v6.0.0`)

## 3. Research releases

For each unique `owner/repo`:

1. List recent releases:
   ```bash
   gh release list -R <owner>/<repo> --limit 30
   ```
2. If GitHub Releases is empty (some actions tag without releases), fall back to tags:
   ```bash
   gh api repos/<owner>/<repo>/tags --paginate | jq -r '.[].name' | head -30
   ```
3. Identify the **latest stable** tag (skip prereleases unless the user already pins one).
4. For each tag between the current ref and latest, fetch release notes:
   ```bash
   gh release view <tag> -R <owner>/<repo>
   ```
   If a tag has no release entry, fall back to the commit log:
   ```bash
   gh api repos/<owner>/<repo>/compare/<current>...<latest> | jq '.commits[].commit.message'
   ```

Special handling:

- **SHA-pinned actions:** treat the inline comment as the human-readable current version. The recommended action becomes "bump to `<new-sha>` (`# vX.Y.Z`)".
- **Branch-pinned actions:** report whether the branch has moved since the last commit the user could have seen, and surface any breaking changes merged on that branch. There is no clean "version" to bump to — the recommendation is usually "review recent commits and either re-pin or migrate to a tag".
- **Major-only tags** (`v6` rather than `v6.0.0`): tag floats within the major. "Outdated" means a newer major exists.

## 4. Assess breaking-change risk

Scan release notes for:

- Major version bumps (`v5` → `v6`)
- Sections marked "BREAKING", "Breaking Changes", "Migration"
- Changed `inputs:` (renamed, removed, made required)
- Changed `outputs:`
- Changed default runtime (Node 16 → Node 20, Node 20 → Node 22)
- Removed sub-actions or path-based usages

For each breaking change, search the workflows and composite action files for usage of the affected feature:

```bash
grep -rnE 'uses:\s*<owner>/<repo>' .github/workflows/ .github/actions/ action.y*ml 2>/dev/null
grep -rA 20 '<owner>/<repo>@' .github/workflows/ .github/actions/ 2>/dev/null | grep -E 'with:|<changed-input>'
```

Cite specific `path:line` references for any input/output the project actually uses. If the project does not pass the changed input or read the changed output, mark risk as Low.

**Runtime-version trap:** if the new major drops a Node runtime version that any self-hosted runner or runner image still uses, flag as blocking. For GitHub-hosted runners this is rarely an issue but worth a one-line check.

## 5. Write the report

Write `tmp/DEPS_UPGRADE_REPORT_ACTIONS.md` using the format in `<skill_dir>/references/report-template.md`, with these adaptations:

- **Emit the Summary table first** — one row per **unique** outdated action (deduped by `owner/repo`, not per source file). Sort breaking-first then alphabetical (`Yes` rows, then `No` rows; alphabetical within each band). Columns: Action, Current → Latest, Breaking? (`Yes`/`No` — no `Hold` for Actions), **Used in** (comma-separated source files — workflows and composite action files), Release notes (direct link to `https://github.com/<owner>/<repo>/releases`).
- Then the **Breaking Changes & Warnings** section, citing the specific files and lines that pass affected inputs.
- Then **per-source-file detail sections** (`## ci.yaml Actions`, `## .github/actions/setup/action.yml Actions`, etc.). An action used in multiple files appears under each — the changelog excerpt can be in the first occurrence with later occurrences linking back ("See [ci.yaml](#ciyaml-actions) above").
- Use `<details>` blocks for changelog excerpts longer than ~30 lines.
- Always include clickable links to the release page (`https://github.com/<owner>/<repo>/releases/tag/<tag>`).

Create `tmp/` if it does not exist. Verify it is gitignored (`grep -qx 'tmp/\?' .gitignore 2>/dev/null`); if not, surface a warning in the return summary.

If no outdated actions are found, do **not** write the report. Return the single-line "no upgrades needed" summary.

## Return value

Return one paragraph summarising:
- Counts per source file (e.g., "ci.yaml: 3 outdated, .github/actions/setup/action.yml: 4 outdated")
- Number of unique actions that need upgrading (deduped across files)
- Number of breaking changes flagged
- Absolute path to the report (or "no upgrades needed")
- Any `tmp/` gitignore warning
