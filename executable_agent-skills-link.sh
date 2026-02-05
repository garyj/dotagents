#!/usr/bin/env bash
# Symlink shared agent skills into each agent's skills directory.
# Source: ~/.agents/skills/<skill>/
# Add new agents to the targets array below.

set -euo pipefail

targets=(
  "$HOME/.claude/skills"
  "$HOME/.codex/skills"
)

mkdir -p "${targets[@]}"

for skill in "$HOME/.agents/skills"/*/; do
  [ -d "$skill" ] || continue
  name="$(basename "$skill")"

  for target in "${targets[@]}"; do
    link="$target/$name"
    if [ -L "$link" ]; then continue; fi
    if [ -d "$link" ]; then rm -rf "$link"; fi
    ln -sf "$HOME/.agents/skills/$name" "$link"
    echo -e "\033[1;32m✓\033[0m $link → ~/.agents/skills/$name"
  done
done
