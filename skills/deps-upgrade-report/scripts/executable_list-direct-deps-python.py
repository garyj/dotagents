#!/usr/bin/python3
# Pinned to /usr/bin/python3 deliberately: $PATH `python3` is often a
# uv-managed interpreter that errors when invoked inside a uv project whose
# requires-python doesn't match. This script only reads pyproject.toml and
# needs nothing from the project's interpreter.
"""List direct Python dependencies grouped by their declaration section.

Reads ./pyproject.toml and prints JSON mapping group -> sorted normalized names:
  - "main"          : [project.dependencies]
  - "optional:<n>"  : [project.optional-dependencies.<n>]
  - "<n>"           : PEP 735 [dependency-groups.<n>]
  - "build-system"  : [build-system].requires (build backends like uv_build,
                      hatchling, setuptools — invisible to `uv tree --outdated`
                      because they aren't in the project venv)

Names are PEP 503 normalized (lowercase, runs of [-_.] -> single dash) so they
match what `uv tree --outdated` emits.
"""
from __future__ import annotations

import json
import re
import sys

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        sys.stderr.write(
            "Need Python 3.11+ (tomllib) or `tomli`. "
            "Try: uv run --with tomli python3 list-direct-deps-python.py\n"
        )
        sys.exit(2)

PEP508_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def extract(spec: str) -> str | None:
    m = PEP508_NAME.match(spec.strip())
    return normalize(m.group(1)) if m else None


def names_from(specs: list) -> list[str]:
    out: set[str] = set()
    for spec in specs:
        if not isinstance(spec, str):
            continue  # PEP 735 include-group entries are dicts; skip
        n = extract(spec)
        if n:
            out.add(n)
    return sorted(out)


def main() -> int:
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        sys.stderr.write("pyproject.toml not found in cwd\n")
        return 1

    groups: dict[str, list[str]] = {}

    project = data.get("project", {}) or {}
    main = names_from(project.get("dependencies", []) or [])
    if main:
        groups["main"] = main

    for name, deps in (project.get("optional-dependencies", {}) or {}).items():
        names = names_from(deps or [])
        if names:
            groups[f"optional:{name}"] = names

    for name, deps in (data.get("dependency-groups", {}) or {}).items():
        names = names_from(deps or [])
        if names:
            groups[name] = names

    build_system = data.get("build-system", {}) or {}
    build_names = names_from(build_system.get("requires", []) or [])
    if build_names:
        groups["build-system"] = build_names

    json.dump(groups, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
