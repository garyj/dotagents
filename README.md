# dotagents

One repo for the instructions and skills every coding agent on this machine loads. Claude Code, Codex, Gemini CLI, pi,
and opencode read the same body and the same skills store through symlinks into this checkout, so an edit here reaches
the next session with no install step.

## Set up a machine

Clone the repo to `~/.agents`, make the symlinks, and enable the commit hook:

```bash
git clone https://github.com/garyj/dotagents ~/.agents
~/.agents/scripts/install
cd ~/.agents && prek install
```

`scripts/install --check` reports what differs and changes nothing. The install never overwrites a real file or
directory. If one is in the way, move it aside and run the install again.

On a machine managed by the dotfiles repo, chezmoi does the clone and the install: a `git-repo` external clones this
repo and a `run_after_` script runs `scripts/install`.

## What each agent reads

| Agent    | Instructions                                        | Skills                                          |
| -------- | --------------------------------------------------- | ----------------------------------------------- |
| claude   | `~/.claude/CLAUDE.md` -> `instructions.md`          | `~/.claude/skills/<name>` -> `skills/<name>`    |
| codex    | `~/.codex/AGENTS.md` -> `instructions.md`           | scans `~/.agents/skills` natively               |
| gemini   | `~/.gemini/GEMINI.md` -> `instructions.md`          | scans `~/.agents/skills` natively               |
| pi       | `~/.pi/agent/AGENTS.md` -> `instructions.md`        | scans `~/.agents/skills` natively               |
| opencode | `~/.config/opencode/AGENTS.md` -> `instructions.md` | no skills feature                               |
| delta    | `~/.config/delta/AGENTS.md` -> `instructions.md`    | not managed here                                |
| grok     | claude's `~/.claude/CLAUDE.md` via its compat scan  | claude's `~/.claude/skills` via its compat scan |
| copilot  | per-repo only                                       | scans `~/.agents/skills` natively               |
| cursor   | per-repo only                                       | not managed here                                |

## Layout

- `instructions.md` is the shared body.
- `skills/<name>/` is one skill per directory. Your own are plain directories.
- `skills/<name>/.provenance.json` marks a copy of someone else's skill, pinned by commit, with a vetting log.
  `skills/<name>/.patches/` holds any local changes as patch files. `scripts/vendor_skill.py` owns those
  directories. Read the `vendor-skill` skill under `.claude/skills/` before adding, updating, or removing one.
- `scripts/install` makes the symlinks in the table above, one per skill for Claude Code. Run it again after adding or
  removing a skill.
- `services/file-host/` hosts agent attachments through Cloudflare Workers and R2. See its [setup guide](services/file-host/SETUP.md).

## Vendored skills

`just skills check` reports which vendored skills changed upstream. `just skills sync` re-copies every pinned commit
plus its patches, which heals a hand edit. `just skills sync --latest NAME` moves one skill to the upstream head and
logs a PENDING vetting entry until you read the new content. To review what moved, open a session here and follow the
`vendor-skill` skill under `.claude/skills/`.

## Skills that chezmoi installs

Skills that ship with a pinned CLI (agent-browser, sentry-cli, worktrunk) and deps-upgrade-report are chezmoi
externals in the dotfiles repo. chezmoi extracts them to `~/.local/share/agent-skills/<name>` and runs
`scripts/install --bridge ~/.local/share/agent-skills`, which symlinks each one into `skills/` and lists it in
`.git/info/exclude`. They are not this repo's to edit. The next `chezmoi apply` restores them.

## Traps

Each of these looks like a gap but is deliberate:

- gemini, copilot, pi, and codex get no skills symlink. They scan `~/.agents/skills` themselves, and a symlink makes
  gemini scan the store twice and warn on every skill. A `~/.codex/skills` link made codex write its `.system/`
  built-ins into this repo.
- claude gets one link per skill, not a link to `skills/`. Claude Code syncs claude.ai skills into
  `~/.claude/skills/synced/`; through a directory link that bucket landed in the shared store, and codex listed it as
  nine more skills with the longest descriptions in its catalogue.
- grok gets no wrapper and no symlink. Its Claude Code compat scan, which has no off switch, already loads
  `~/.claude/CLAUDE.md` and `~/.claude/skills`. Adding `~/.grok/AGENTS.md` or `~/.grok/skills` loads everything
  twice.
- grok truncates each rules file at 10,000 characters. Check `wc -c instructions.md` before growing it. grok warns
  when it clips.
- delta reads `AGENT.md` before `AGENTS.md` in `~/.config/delta`. A non-empty `AGENT.md` there hides the link.
- Claude Code in a Cowork session skips a `~/.claude/CLAUDE.md` that is itself a symlink, so it runs there without
  `instructions.md`.
- Claude Code's Edit and Write tools refuse to write through a symlink. Edit `instructions.md` by its real path, not
  as `~/.claude/CLAUDE.md`.
