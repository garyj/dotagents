# dotagents

This checkout is the live agent config. Every agent's global instruction file is a symlink to `instructions.md`, so a
saved edit reaches the next agent session with no install step, and a broken `instructions.md` breaks every agent at
once.

- A `skills/<name>/.provenance.json` marks a copy of someone else's skill, owned by `scripts/vendor_skill.py` with
  local changes in `.patches/`. Never hand-edit one without capturing the edit as a patch. Read
  `.claude/skills/vendor-skill/SKILL.md` before adding, updating, patching, or removing one.
- Run `scripts/install` after adding or removing a skill so `~/.claude/skills/` gets or loses its link.
- Symlinks in `skills/` that point outside the repo belong to chezmoi and are listed in `.git/info/exclude`. Leave
  them alone.
- README.md carries the per-agent wiring table and the traps. Read it before changing how any file is found.

There is no test suite. Validate with `just skills sync --dry-run` (every vendored copy matches its pin), `just skills
check` (the only command that shows a patch that no longer applies), and `scripts/install --check`.

A prek hook scans staged files for hidden Unicode. Run `prek install` once per clone.

Work directly on `master` in this checkout. Create a worktree or branch only when the user asks for one.

Commit messages start with a lowercase verb and colon (`add: ...`, `update: ...`, `fix: ...`). Do not commit without
explicit approval.
