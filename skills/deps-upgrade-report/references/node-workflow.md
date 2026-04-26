# Node (npm) Workflow

Procedure for the Node agent spawned by the deps-upgrade-report skill. Run from the project root.

## 1. Gather outdated dependencies

```bash
npm outdated --json || true
```

`npm outdated` exits non-zero **when packages are outdated** — that is the success path here, so `|| true` keeps the pipeline going. The JSON is keyed by package name with `current`, `wanted`, `latest`, `type` (one of `dependencies`/`devDependencies`/`peerDependencies`/`optionalDependencies`), and `homepage` fields.

If the command produces no JSON output (truly empty `{}`), there are no upgrades — skip to the "no upgrades needed" return path.

## 2. Filter to direct dependencies

Run the helper:

```bash
<skill_dir>/scripts/list-direct-deps-node.sh
```

It prints JSON like:

```json
{
  "dependencies": ["next", "react"],
  "devDependencies": ["typescript", "vitest"]
}
```

Each outdated entry from step 1 carries a `type` field — use that for grouping. Drop any outdated entry whose name is not in the direct-dep map (transitive).

## 3. Research changelogs

For each outdated direct dependency:

1. Find the project URL: `npm view <name> repository.url homepage --json`
2. If GitHub-hosted, prefer `gh` over web scraping:
   - `gh release list -R <owner>/<repo> --limit 30`
   - `gh release view <tag> -R <owner>/<repo>` for each tag between current and latest
3. Otherwise web search: `<package> changelog` or `<package> release notes`
4. If no changelog can be located, mark "Changelog not found" with a link to `https://www.npmjs.com/package/<name>`

Extract entries strictly between current and latest. Summarise concisely while preserving enough detail to skim.

## 4. Assess breaking-change risk

Scan changelog excerpts for:
- Major version bumps (semver) — assume potentially breaking
- **0.x packages: any minor bump is potentially breaking**
- Sections marked "BREAKING", "Breaking Changes", "Migration"
- Removed / renamed exports, changed defaults, dropped Node version support, ESM-only conversions

For each breaking change, grep the project source for usage of the affected import/API. State whether the project actually touches it and cite specific files (`src/foo.ts:42`).

**Cross-check runtime and peer requirements.** For every upgrade candidate, check the new version's `engines.node`, `engines.npm`, and peer-dependency declarations (`npm view <name>@<latest> engines peerDependencies --json`). If any exceed what `package.json#engines` declares, or conflict with existing peer deps, flag it as a **blocking constraint** in the Breaking Changes & Warnings section with a clear "bump X first, or pin to the last compatible version Y" recommendation. Engine-version mismatches will not show up in changelogs as "BREAKING" but will silently break installs or runtime.

## 5. Write the report

Write `tmp/DEPS_UPGRADE_REPORT_NODE.md` using the format in `<skill_dir>/references/report-template.md`.

- **Emit the Summary table first** — one row per outdated direct dep, sorted breaking-first then alphabetical (`Yes` rows, then `No` rows; alphabetical within each band). Columns: Package, Current → Latest, Breaking? (`Yes`/`No` — no `Hold` for Node), Group (npm dep type: `dependencies`/`devDependencies`/`peerDependencies`/`optionalDependencies`), Changelog (direct link).
- Then the **Breaking Changes & Warnings** section (engine/peer mismatches go here as well, flagged Yes).
- Then **per-group detail sections** by npm dep type with full changelog excerpts.
- Use `<details>` blocks for changelog excerpts longer than ~30 lines.
- Always include clickable links to changelogs — the Summary table link and the per-group section link should point to the same canonical URL.

Create `tmp/` if it does not exist. Verify it is gitignored (`grep -qx 'tmp/\?' .gitignore 2>/dev/null`); if not, warn in the return summary so the user can add it before committing.

If no outdated direct deps are found, do **not** write the report. Return the single-line "no upgrades needed" summary instead.

## Return value

Return one paragraph summarising:
- Counts per group (e.g., "dependencies: 3 outdated, devDependencies: 5 outdated")
- Number of breaking changes flagged
- Absolute path to the report file (or "no upgrades needed")
- Any `tmp/` gitignore warning
