#!/usr/bin/env bash
# List direct Node dependencies from ./package.json grouped by dep type.
# Emits JSON: {"dependencies":[...],"devDependencies":[...], ...}
# Empty groups are omitted.

set -euo pipefail

if [ ! -f package.json ]; then
  echo "package.json not found in cwd" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required but not on PATH" >&2
  exit 2
fi

jq '{
  dependencies:         (.dependencies         // {} | keys),
  devDependencies:      (.devDependencies      // {} | keys),
  peerDependencies:     (.peerDependencies     // {} | keys),
  optionalDependencies: (.optionalDependencies // {} | keys)
} | with_entries(select(.value | length > 0))' package.json
