# dotagents

This checkout is the live agent config. `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, and the other agents' global
instruction files are symlinks to `instructions.md`, and `~/.claude/skills` and `~/.codex/skills` are symlinks to
`skills/`. A saved edit reaches the next agent session with no install step, so a broken `instructions.md` breaks every
agent at once.

- `instructions.md` is the shared body. `docs/` holds the files it includes by path.
- `skills/<name>/` is one skill. A `.provenance.json` marks a copy of someone else's skill, owned by
  `scripts/vendor_skill.py` with local changes in `.patches/`. Never hand-edit one without capturing the edit as a
  patch. Invoke the `vendor-skill` skill before adding, updating, patching, or removing one.
- Symlinks in `skills/` that point outside the repo belong to chezmoi and are listed in `.git/info/exclude`. Leave
  them alone.
- README.md carries the per-agent wiring table and the traps. Read it before changing how any file is found.

There is no test suite. Validate with `just skills sync --dry-run` (every vendored copy matches its pin) and
`scripts/install --check`.

A prek hook scans staged files for hidden Unicode. Run `prek install` once per clone.

Commit messages start with a lowercase verb and colon (`add: ...`, `update: ...`, `fix: ...`). Do not commit without
explicit approval.
