# Report Template

Use this structure for each report file. Three top-level sections in order: **Summary** (skim index), **Breaking Changes & Warnings** (priority risks), **per-group detail sections** (full changelog excerpts).

The Summary table exists so a reader can scan the whole upgrade cycle in one view, click straight through to changelogs they want to read in depth, and only drop into the prose sections for entries flagged Yes/Hold.

---

```markdown
# Dependency Upgrade Report — [Python/Node/Actions]

Generated: [YYYY-MM-DD]

---

## Summary

| Package | Current → Latest | Breaking? | Group | Changelog |
|---|---|---|---|---|
| django | 6.0.2 → 6.0.4 | No | main | [Release notes](https://github.com/django/django/releases) |
| django-allauth | 65.14.3 → 65.16.1 | Yes | main | [Changelog](https://docs.allauth.org/en/latest/release-notes/recent.html) |
| posthog | 5.7.0 → 6.2.0 | Hold | main | [Releases](https://github.com/PostHog/posthog-python/releases) |
| pytest | 9.0.2 → 9.0.3 | No | test | [Release notes](https://github.com/pytest-dev/pytest/releases) |

---

## Breaking Changes & Warnings

> **If no breaking changes are found, replace this section with:**
> No breaking changes detected in this upgrade cycle.

### [package-name] [current] → [new]

**What changed:** [brief description of the breaking change]

**Risk to this project:** [High/Medium/Low] — [explanation of whether and how it affects the codebase, referencing specific files/usages found]

**Recommended action:** [what to do — e.g., "Update import from X to Y in src/foo.py", "Test thoroughly, API signature changed"]

---

## [Group Name] Dependencies
<!-- e.g., "Main Dependencies", "Dev Dependencies", "Test Dependencies" -->

### [package-name] — [current version] → [new version]

[Changelog](https://link-to-changelog)

#### Changes ([current] → [new])

<!-- For short changelogs (under ~30 lines), include directly: -->

- [changelog entry 1]
- [changelog entry 2]
- ...

<!-- For long changelogs (over ~30 lines), use a collapsible block: -->

<details>
<summary>Full changelog ([current] → [new])</summary>

[full changelog content here]

</details>

---

<!-- Repeat ### block for each dependency in the group -->
<!-- Repeat ## block for each dependency group -->
```

## Summary table — column conventions

**Population:** one row per outdated direct entry. Sort breaking-first then alphabetical:
1. `Yes` rows
2. `Hold` rows
3. `No` rows
Within each band, alphabetical by package name.

**Columns:**

| Column | Meaning |
|---|---|
| Package / Action | Name as it appears in `pyproject.toml` / `package.json` / `uses:` |
| Current → Latest | Versions as the agent saw them; for Holds, still show the latest available release on the right of the arrow |
| Breaking? | `Yes` (entry exists in Breaking Changes section) / `No` / `Hold` (deliberate version cap, Python only) |
| Group / Used in | Python: dependency group (`main`, `dev`, `test`, `optional:*`). Node: dep type (`dependencies`, `devDependencies`, etc.). Actions: comma-separated workflow filenames where the action appears |
| Changelog / Release notes | Direct link to the canonical changelog or releases page (GitHub Releases > CHANGELOG.md > package homepage) |

## Actions report — column variant

For `DEPS_UPGRADE_REPORT_ACTIONS.md`, swap the **Group** column for **Used in**:

```markdown
| Action | Current → Latest | Breaking? | Used in | Release notes |
|---|---|---|---|---|
| googleapis/release-please-action | v4 → v5 | Yes | ci.yaml | [Releases](https://github.com/googleapis/release-please-action/releases) |
| actions/checkout | v5 → v6 | No | ci.yaml, docs.yml | [Releases](https://github.com/actions/checkout/releases) |
```

The `Breaking?` column has no `Hold` value for Actions — only `Yes` / `No`.
