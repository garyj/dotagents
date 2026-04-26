# GitHub Actions Workflow

Procedure for the GitHub Actions agent spawned by the deps-upgrade-report skill. Run from the project root.

## 1. Gather and group action references

Run the helper:

```bash
<skill_dir>/scripts/list-direct-actions.py
```

It emits JSON keyed by workflow filename, with each entry recording `action`, `ref`, source `line`, and any inline `comment`:

```json
{
  "ci.yaml": [
    {"action": "actions/checkout", "ref": "v6", "line": 42},
    {"action": "actions/setup-python", "ref": "v6", "line": 51}
  ],
  "release-deployment.yaml": [
    {"action": "googleapis/release-please-action", "ref": "v4", "line": 18}
  ]
}
```

Local actions (`./...`) and Docker actions (`docker://...`) are skipped — only third-party `owner/repo@ref` references are returned.

## 2. Deduplicate to a unique action set

Build a unique map of `owner/repo` -> `{refs_seen: set, used_in: [filename:line, ...]}`. Multiple workflows pinning the same action at the same ref are common — research each `owner/repo` once but report the per-workflow usage so the user knows what they'll be touching.

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

For each breaking change, search the workflows for usage of the affected feature:

```bash
grep -nE 'uses:\s*<owner>/<repo>' .github/workflows/*.y*ml
grep -A 20 '<owner>/<repo>@' .github/workflows/*.y*ml | grep -E 'with:|<changed-input>'
```

Cite specific `workflow.yaml:line` references for any input/output the project actually uses. If the project does not pass the changed input or read the changed output, mark risk as Low.

**Runtime-version trap:** if the new major drops a Node runtime version that any self-hosted runner or runner image still uses, flag as blocking. For GitHub-hosted runners this is rarely an issue but worth a one-line check.

## 5. Write the report

Write `tmp/DEPS_UPGRADE_REPORT_ACTIONS.md` using the format in `<skill_dir>/references/report-template.md`, with these adaptations:

- **Emit the Summary table first** — one row per **unique** outdated action (deduped by `owner/repo`, not per workflow file). Sort breaking-first then alphabetical (`Yes` rows, then `No` rows; alphabetical within each band). Columns: Action, Current → Latest, Breaking? (`Yes`/`No` — no `Hold` for Actions), **Used in** (comma-separated workflow filenames), Release notes (direct link to `https://github.com/<owner>/<repo>/releases`).
- Then the **Breaking Changes & Warnings** section, citing the specific workflow files and lines that pass affected inputs.
- Then **per-workflow-file detail sections** (`## ci.yaml Actions`, `## release-deployment.yaml Actions`, etc.). An action used in multiple workflows appears under each — the changelog excerpt can be in the first occurrence with later occurrences linking back ("See [ci.yaml](#ciyaml-actions) above").
- Use `<details>` blocks for changelog excerpts longer than ~30 lines.
- Always include clickable links to the release page (`https://github.com/<owner>/<repo>/releases/tag/<tag>`).

Create `tmp/` if it does not exist. Verify it is gitignored (`grep -qx 'tmp/\?' .gitignore 2>/dev/null`); if not, surface a warning in the return summary.

If no outdated actions are found, do **not** write the report. Return the single-line "no upgrades needed" summary.

## Return value

Return one paragraph summarising:
- Counts per workflow file (e.g., "ci.yaml: 3 outdated, release-deployment.yaml: 1 outdated")
- Number of unique actions that need upgrading (deduped across files)
- Number of breaking changes flagged
- Absolute path to the report (or "no upgrades needed")
- Any `tmp/` gitignore warning
