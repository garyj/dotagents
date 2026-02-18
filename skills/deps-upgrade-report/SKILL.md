---
name: deps-upgrade-report
description: Generate a dependency upgrade report for outdated packages. Detects the project's package managers (uv/Python and npm/Node), checks for outdated direct dependencies, fetches changelogs from the internet, and produces a skimmable markdown report with breaking change warnings. Use when the user asks to "check for outdated dependencies", "dependency upgrade report", "what needs updating", "review dependency updates", "monthly dependency audit", or any variation of checking/reporting on outdated packages.
---

# Dependency Upgrade Report

Generate comprehensive, skimmable markdown reports for outdated direct dependencies. Supports Python (uv) and Node (npm) projects. Produces separate report files per package manager.

## Workflow

1. Detect package managers
2. Gather outdated dependencies
3. Filter to direct dependencies only
4. Research changelogs for each dependency
5. Identify breaking changes and assess project impact
6. Generate report(s)

## Step 1: Detect Package Managers

Check the project root for configuration files:

- **Python/uv**: `pyproject.toml` exists AND `uv` is available on PATH
- **Node/npm**: `package.json` exists AND `npm` is available on PATH

Run for whichever managers are detected. If neither is found, inform the user.

## Step 2: Gather Outdated Dependencies

### Python (uv)

Run: `uv tree --outdated --all-groups --depth 2`

This shows the full dependency tree with outdated markers. Parse the output to identify packages with version mismatches.

### Node (npm)

Run: `npm outdated --json`

This returns a JSON object keyed by package name with `current`, `wanted`, and `latest` versions.

## Step 3: Filter to Direct Dependencies Only

Only report on dependencies that are **directly declared** by the project:

- **Python**: Read `pyproject.toml` and extract package names from `[project.dependencies]`, `[project.optional-dependencies.*]`, and all `[dependency-groups.*]` sections. Map these to the dependency groups they belong to (e.g., "main", "dev", "test").
- **Node**: Read `package.json` and extract package names from `dependencies`, `devDependencies`, `peerDependencies`, and `optionalDependencies`. Map these to their respective groups.

Discard any outdated transitive dependencies not directly declared.

## Step 4: Research Changelogs

For each outdated direct dependency, use web search to find the changelog or release notes. Typical sources:

- GitHub releases page (most common)
- CHANGELOG.md in the repository
- PyPI/npm package page linking to release notes
- Read the Docs or official documentation

Extract the relevant entries between the current version and the latest version. Summarize concisely but include enough detail to skim. If a changelog cannot be found, note it as "Changelog not found" with a link to the package's homepage.

## Step 5: Identify Breaking Changes

Scan the changelog entries for:

- Major version bumps (semver)
- Entries explicitly marked as "BREAKING", "Breaking Changes", or "Migration"
- Deprecation removals
- API signature changes

For each breaking change found, assess whether it could affect the current project by:

1. Searching the codebase for usage of the affected API/feature
2. Noting whether the project uses the changed functionality

## Step 6: Generate Report

Output separate reports per package manager:

- **Python**: `tmp/DEPS_UPGRADE_REPORT_PYTHON.md`
- **Node**: `tmp/DEPS_UPGRADE_REPORT_NODE.md`

If only one package manager is detected, still use the suffixed filename for consistency.

Create the `tmp/` directory if it doesn't exist.

Use the report template in [references/report-template.md](references/report-template.md) for the exact output format.

### Key formatting rules

- Group dependencies by their declaration group (e.g., main, dev, test)
- Include the full changelog excerpt inline so the user can skim one file
- Breaking changes section goes at the TOP, before the per-group sections
- Always include clickable links to changelogs
- Use collapsible `<details>` blocks for long changelog excerpts (more than ~30 lines)
