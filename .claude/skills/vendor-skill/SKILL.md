---
name: vendor-skill
description: Use when adding, updating, patching, vetting, or removing a third-party agent skill under skills/. Covers the vendored-vs-chezmoi-external decision, the .provenance.json schema, the patch layer, and what vetting has to catch.
---

# Vendoring a third-party skill

`scripts/vendor_skill.py` (`just skills`) owns every write into a vendored directory. What is on disk is upstream bytes
at the pinned commit plus the patches in the skill's `.patches/` directory. A hand edit reads as drift, and the next sync
overwrites it, unless you capture it as a patch.

## Vendor it, or let chezmoi fetch it?

A skill that ships with a pinned CLI belongs with the CLI's pin. Add it as an archive external in the dotfiles repo
(`home/.chezmoiexternal.toml.tmpl`, target `.local/share/agent-skills/<name>`) with the version from
`.chezmoidata.yaml`, the way agent-browser, sentry-cli, and worktrunk are done. chezmoi extracts it and
`scripts/install --bridge` links it into `skills/`, so the skill and the binary move together and Renovate bumps both.

Vendor it here when it is a standalone skill with no binary to track, which is most skill repos. The content lands in
the diff, pinned by commit, and `just skills check` reports when upstream moves.

## Adding one

1. Write `skills/<name>/.provenance.json`:

   ```json
   {
     "source": "https://github.com/owner/repo",
     "path": "skills/name",
     "commit": "<full sha>",
     "vetted": ["PENDING"]
   }
   ```

   `path` is the subpath inside the upstream repo and may be a directory or a single file. `commit` is the repo revision
   you take the content from, usually the default-branch head.
2. `just skills sync <name>` fetches that commit and writes the files.
3. Vet what landed, then replace `PENDING` with the date, how you checked, and a verdict.

## What vetting has to catch

Read every line. Past what the skill tells an agent to run and whether it sends anything outward (hidden Unicode the
prek hook already scans for), two failure modes are specific to skills:

- **Another agent's paths.** A skill written for one agent hardcodes its layout, so a Cursor-native transcript path like
  `~/.cursor/projects/<slug>/agent-transcripts/` finds nothing here.
- **Delegation to skills that are not here.** A skill lifted out of a bundle hands work to its siblings; unless those
  are vendored too, the steps that call them are undefined.

Neither is grounds for rejection on its own, but the vetting entry has to say so plainly: the skill lands in `skills/`
and every agent loads it. `disable-model-invocation: true` in the frontmatter makes it explicit-request-only, capping
the blast radius of one that is not fully usable yet.

## Changing one: mostly, don't

Vendored means verbatim. Put your changes outside the file, where they cannot conflict with upstream: the global
instructions, a wrapper on PATH, config. The clean-exit gate and the P1 default for autoreview live in instructions.md
and `~/bin/autoreview`, and have survived every upstream rewrite untouched.

A patch is for a one-line mechanical change only, such as a frontmatter flag:

```bash
just skills patch <name> <slug> --why "One line on why the change exists."
```

That writes `skills/<name>/.patches/NNN-<slug>.patch` with the `--why` line as its header, and every sync applies it
after copying upstream. When a patch stops applying, delete it and decide again. Never re-derive it: the conflict means
upstream changed that spot, so read it fresh. If you want to reshape a skill, fork it (drop the provenance) or write
your own, and accept that upstream fixes stop arriving.

## Reviewing what moved

Run this in a session in this repo when you want to know what upstream did since the pins.

1. `just skills check` lists the skills that moved and how many files changed.
2. For each one worth taking, `just skills sync --latest <name>`. The sync log names any patch that stopped
   applying, and `.provenance.json` gets a PENDING vetting entry.
3. Read the upstream change: `gh api repos/<owner>/<repo>/compare/<old>...<new>` gives the commits and per-file
   patches. It omits `patch` for large files; fetch both versions with `gh api repos/<owner>/<repo>/contents/<path>?ref=<sha>`
   and diff them. Skip test bodies; their line counts are enough.
4. Report back, then stop: what changed for an agent's behaviour, anything on the vetting checklist above, patches
   that broke, rules the current model already follows without being told, and a proposed vetting entry. A short page,
   not a wall. Offer it as an artifact when a page reads better than the terminal.
5. On garyj's go: capture any edit with `just skills patch`, replace the PENDING entry in `.provenance.json` with the
   agreed one, commit.

## Updating

`just skills check` reports which upstreams moved a skill's own bytes; unrelated commits in the same repo do not count.
`just skills sync --latest <name>` takes the new content, applies the patches, and appends a PENDING entry to `vetted`
naming any patch that no longer applies. Plain `just skills sync` re-copies the pinned commit, healing drift; add
`--dry-run` to report it and exit non-zero.

## Removing

`git rm -r skills/<name>`. Nothing else references it.
