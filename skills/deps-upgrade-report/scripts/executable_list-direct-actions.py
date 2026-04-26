#!/usr/bin/python3
# Pinned to /usr/bin/python3 deliberately: $PATH `python3` is often a
# uv-managed interpreter that errors when invoked inside a uv project whose
# requires-python doesn't match. This script only reads workflow YAML and
# needs nothing from the project's interpreter.
"""List third-party GitHub Actions referenced in ./.github/workflows/*.y*ml.

Emits JSON keyed by workflow filename:

  {
    "ci.yaml": [
      {"action": "actions/checkout", "ref": "v6", "line": 42},
      ...
    ],
    ...
  }

Skips local composite actions (`./...`) and Docker actions (`docker://...`).
Deduplicates within a single workflow file but preserves cross-file duplicates
so the consumer can see which workflows reference each action.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Matches lines like:
#   uses: actions/checkout@v6
#   - uses: 'actions/checkout@v6'
#   uses: actions/checkout@8f4b7f8  # v6.0.0
USES_RE = re.compile(r"^\s*-?\s*uses:\s*['\"]?([^'\"\s#]+)['\"]?\s*(?:#\s*(.*))?$")


def parse_uses(value: str) -> tuple[str, str] | None:
    if value.startswith("./") or value.startswith("docker://"):
        return None
    if "@" not in value:
        return None
    action, ref = value.rsplit("@", 1)
    return action, ref


def main() -> int:
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.is_dir():
        sys.stderr.write(".github/workflows/ not found in cwd\n")
        return 1

    out: dict[str, list[dict]] = {}
    for path in sorted(workflows_dir.iterdir()):
        if path.suffix not in (".yml", ".yaml"):
            continue

        actions: list[dict] = []
        seen: set[tuple[str, str]] = set()
        try:
            text = path.read_text()
        except OSError as exc:
            sys.stderr.write(f"failed to read {path}: {exc}\n")
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            m = USES_RE.match(line)
            if not m:
                continue
            parsed = parse_uses(m.group(1))
            if not parsed:
                continue
            action, ref = parsed
            if (action, ref) in seen:
                continue
            seen.add((action, ref))
            entry: dict = {"action": action, "ref": ref, "line": lineno}
            comment = m.group(2)
            if comment:
                entry["comment"] = comment.strip()
            actions.append(entry)

        if actions:
            out[path.name] = actions

    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
