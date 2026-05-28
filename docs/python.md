---
name: python
description: Python tooling preferences. Use when starting, packaging, or running Python projects to standardise on uv and pyproject.toml.
license: MIT
---

# Preamble

When you load this file, say "Python preferences loaded"

# Python

- I prefer to use uv for everything (uv add, uv run, etc)
- Do not use old fashioned methods for package management like poetry, pip or easy_install.
- Make sure that there is a pyproject.toml file in the root directory.
- If there isn't a pyproject.toml file, create one using uv by running uv init.
