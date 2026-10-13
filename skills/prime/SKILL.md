---
name: prime
description: Get up to speed on a repository at the start of a task, from its git state, layout, stack, rules file, and README. Invoked by the user as /prime or $prime.
disable-model-invocation: true
---

# Prime

Run these from the repository root and read the output; do not paste it back.

- `git status --short` and `git log --oneline -10`
- `{ git ls-files; git ls-files --others --exclude-standard; } | cut -d/ -f1-2 | sort -u | head -60` for the layout
- the first 20 lines of any `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, or `composer.json`
  at the root
- `AGENTS.md`, else `CLAUDE.md`, else `COPILOT.md`, if any
- the first 80 lines of `README.md`, if any

Then report, under 200 words: the project type and stack in one line, three to five key directories, the current
branch and uncommitted changes, the area relevant to the task if one was given, and any conventions or traps worth
remembering. Do not read other files unless asked.
