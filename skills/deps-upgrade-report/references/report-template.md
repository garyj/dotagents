# Report Template

Use this exact structure for each report file. Adapt section counts as needed.

---

```markdown
# Dependency Upgrade Report — [Python/Node]

Generated: [YYYY-MM-DD]

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
