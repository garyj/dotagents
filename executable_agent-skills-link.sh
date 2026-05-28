#!/usr/bin/env bash
# Symlink shared agent skills and AGENTS.md into each agent's directory.
# Skills source: ~/.agents/skills/<skill>/
# AGENTS.md source: ~/.agents/AGENTS.md (linked under each agent's expected filename,
#   e.g. CLAUDE.md for Claude, GEMINI.md for Gemini, AGENTS.md elsewhere).
#
# To add a new agent, append an entry to the agents array below in the form
# "<agent root>:<agents.md filename>". Example for Gemini:
#   "$HOME/.gemini:GEMINI.md"

set -euo pipefail

# Each entry: "<agent root>:<agents.md filename>"
agents=(
  "$HOME/.claude:CLAUDE.md"
  "$HOME/.codex:AGENTS.md"
)

agents_md="$HOME/.agents/AGENTS.md"

for entry in "${agents[@]}"; do
  root="${entry%%:*}"
  agents_name="${entry##*:}"
  skills_dir="$root/skills"

  mkdir -p "$skills_dir"

  for skill in "$HOME/.agents/skills"/*/; do
    [ -d "$skill" ] || continue
    name="$(basename "$skill")"
    link="$skills_dir/$name"
    if [ -L "$link" ]; then continue; fi
    if [ -d "$link" ]; then rm -rf "$link"; fi
    ln -sf "$HOME/.agents/skills/$name" "$link"
    echo -e "\033[1;32m✓\033[0m $link → ~/.agents/skills/$name"
  done

  if [ -f "$agents_md" ]; then
    md_link="$root/$agents_name"
    if [ ! -L "$md_link" ]; then
      [ -e "$md_link" ] && rm -f "$md_link"
      ln -sf "$agents_md" "$md_link"
      echo -e "\033[1;32m✓\033[0m $md_link → ~/.agents/AGENTS.md"
    fi
  fi
done
