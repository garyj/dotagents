#!/usr/bin/python3
# Pinned to /usr/bin/python3 deliberately: $PATH `python3` is often a
# uv-managed interpreter that errors when invoked inside a uv project whose
# requires-python doesn't match. This script only reads workflow YAML and
# needs nothing from the project's interpreter.
"""List third-party GitHub Actions referenced by this repository.

Scans:
  - workflow files:        .github/workflows/*.y*ml
  - composite/local action definitions: .github/actions/**/action.y*ml
    and action.yml / action.yaml at the repo root
  - any other local action reached via `uses: ./path` (resolved to its
    action.yml/action.yaml and scanned recursively)

Emits JSON keyed by repo-relative file path:

  {
    ".github/workflows/ci.yaml": [
      {"action": "actions/checkout", "ref": "v6", "line": 42},
      ...
    ],
    ".github/actions/setup/action.yml": [
      {"action": "astral-sh/setup-uv", "ref": "v7", "line": 11},
      ...
    ]
  }

Reusable-workflow references (`uses: owner/repo/.github/workflows/x.yml@ref`)
are included with `"type": "reusable-workflow"`, `action` set to `owner/repo`,
and the workflow path in `"workflow"`.

Skips Docker actions (`docker://...`). Local `./...` references are followed,
not reported as entries themselves. Deduplicates within a single file but
preserves cross-file duplicates so the consumer can see which files reference
each action.
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

REUSABLE_RE = re.compile(r"^([^/]+/[^/]+)/(.+\.ya?ml)$")


def parse_uses(value: str) -> dict | None:
    """Classify a `uses:` value into an entry dict, or None to skip.

    Local `./...` references are returned as {"local": <path>} for the caller
    to resolve and recurse into.
    """
    if value.startswith("docker://"):
        return None
    if value.startswith("./"):
        return {"local": value}
    if "@" not in value:
        return None
    target, ref = value.rsplit("@", 1)
    m = REUSABLE_RE.match(target)
    if m:
        return {
            "action": m.group(1),
            "workflow": m.group(2),
            "ref": ref,
            "type": "reusable-workflow",
        }
    return {"action": target, "ref": ref}


def resolve_local(value: str) -> Path | None:
    """Resolve a `uses: ./path` reference to its action definition file."""
    rel = Path(value[2:] or ".")
    if rel.suffix in (".yml", ".yaml"):
        # Local reusable workflow (./.github/workflows/x.yml) — that file is
        # already in the scan set, or a direct file reference.
        return rel if rel.is_file() else None
    for name in ("action.yml", "action.yaml"):
        candidate = rel / name
        if candidate.is_file():
            return candidate
    return None


def scan_file(path: Path) -> tuple[list[dict], list[str]]:
    """Extract action entries and local `./...` references from one file."""
    entries: list[dict] = []
    locals_: list[str] = []
    seen: set[tuple[str, str]] = set()
    try:
        text = path.read_text()
    except OSError as exc:
        sys.stderr.write(f"failed to read {path}: {exc}\n")
        return entries, locals_

    for lineno, line in enumerate(text.splitlines(), start=1):
        m = USES_RE.match(line)
        if not m:
            continue
        parsed = parse_uses(m.group(1))
        if not parsed:
            continue
        if "local" in parsed:
            locals_.append(parsed["local"])
            continue
        key = (parsed["action"], parsed["ref"])
        if key in seen:
            continue
        seen.add(key)
        entry: dict = dict(parsed, line=lineno)
        comment = m.group(2)
        if comment:
            entry["comment"] = comment.strip()
        entries.append(entry)

    return entries, locals_


def initial_files() -> list[Path]:
    files: list[Path] = []
    workflows_dir = Path(".github/workflows")
    if workflows_dir.is_dir():
        files.extend(
            p for p in sorted(workflows_dir.iterdir())
            if p.suffix in (".yml", ".yaml")
        )
    actions_dir = Path(".github/actions")
    if actions_dir.is_dir():
        for name in ("action.yml", "action.yaml"):
            files.extend(sorted(actions_dir.rglob(name)))
    for name in ("action.yml", "action.yaml"):
        root_action = Path(name)
        if root_action.is_file():
            files.append(root_action)
    return files


def main() -> int:
    queue = initial_files()
    if not queue:
        sys.stderr.write(
            "no workflow or action definition files found in cwd\n"
        )
        return 1

    out: dict[str, list[dict]] = {}
    scanned: set[str] = set()
    while queue:
        path = queue.pop(0)
        key = path.as_posix()
        if key in scanned:
            continue
        scanned.add(key)

        entries, local_refs = scan_file(path)
        if entries:
            out[key] = entries

        for ref in local_refs:
            resolved = resolve_local(ref)
            if resolved is None:
                sys.stderr.write(
                    f"{key}: could not resolve local action {ref!r}\n"
                )
                continue
            if resolved.as_posix() not in scanned:
                queue.append(resolved)

    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
