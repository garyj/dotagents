#!/usr/bin/env bash
# Detect which dependency surfaces this project uses for the deps-upgrade-report skill.
# Emits JSON: {"python":bool,"node":bool,"actions":bool}
# A surface is "detected" only when both the config file AND the required CLI are present.

set -euo pipefail

python_ok=false
node_ok=false
actions_ok=false

if [ -f pyproject.toml ] && command -v uv >/dev/null 2>&1; then
  python_ok=true
fi

if [ -f package.json ] && command -v npm >/dev/null 2>&1; then
  node_ok=true
fi

if [ -d .github/workflows ] && command -v gh >/dev/null 2>&1 \
   && [ -n "$(find .github/workflows -maxdepth 1 \( -name '*.yml' -o -name '*.yaml' \) -print -quit 2>/dev/null)" ]; then
  actions_ok=true
fi

printf '{"python":%s,"node":%s,"actions":%s}\n' "$python_ok" "$node_ok" "$actions_ok"
