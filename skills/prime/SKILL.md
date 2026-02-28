---
name: prime
description: Understand the codebase and project structure. When starting a new task, use this skill to get up to speed on the project context, rules, and conventions.
---

## Project context

- Git status: !`git status --short`
- Recent commits: !`git log --oneline -10`
- Directory structure: !`{ git ls-files; git ls-files --others --exclude-standard; } 2>/dev/null | cut -d/ -f1-2 | sort -u | head -60`
- Stack hints: !`find . -maxdepth 1 \( -name "package.json" -o -name "pyproject.toml" -o -name "Cargo.toml" -o -name "go.mod" -o -name "pom.xml" -o -name "composer.json" \) -exec echo "=== {} ===" \; -exec head -20 {} \; 2>/dev/null`

## Rules & conventions

!`cat AGENTS.md 2>/dev/null || cat CLAUDE.md 2>/dev/null || cat COPILOT.md 2>/dev/null || echo "No rules file found"`

## README (summary)

!`head -80 README.md 2>/dev/null || echo "No README found"`

## Your task

Report a brief structured summary:

- **Project type & stack** (1 line)
- **Key directories** (3–5 bullets)
- **Current branch / uncommitted changes**
- **Relevant area for the task** (if a task was described)
- Any conventions or gotchas to remember

Keep the report under ~200 words. Do not read additional files unless asked.
