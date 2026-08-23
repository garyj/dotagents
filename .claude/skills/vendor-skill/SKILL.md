---
name: vendor-skill
description: Use when adding, updating, vetting, or removing a third-party agent skill under home/dot_agents/skills/. Covers the externals-vs-vendored decision, the dot_provenance schema, and what vetting has to catch.
---

# Vendoring a third-party skill

`scripts/vendor_skill.py` (`just skills`) owns every write into a vendored directory, because the copy has to stay
byte-identical to upstream and sit under chezmoi's filename attributes (`executable_`, `symlink_`, `dot_`). A hand-edit
reads as drift, and the next sync overwrites it.

## Vendor it, or make it an external?

If upstream tags releases, it does not belong here at all. Add it to `home/.chezmoiexternal.toml.tmpl` with a version
pin in `.chezmoidata.yaml`, the way agent-browser, sentry-cli and worktrunk are done, and let Renovate bump it. chezmoi
is the fetcher there, so moving the pin is the entire update.

Vendor it when upstream has no releases, which is most skill repos, or when the content itself should land in the diff.
Renovate cannot maintain those on its own: it advances a pin but cannot copy files, so the provenance would lie.

## Adding one

1. Write `home/dot_agents/skills/<name>/dot_provenance` with `source`, `path`, and `commit` (all required), plus
   `vetted: PENDING`. `path` is the subpath inside the upstream repo and may be a directory or a single file.
2. `just skills sync <name>` fetches that commit and writes the files.
3. Vet what landed, then replace `vetted` with the date, how you checked, and a verdict.

## What vetting has to catch

Read every line. Past what the skill tells an agent to run and whether it sends anything outward (hidden Unicode the
prek hook already scans for), two failure modes are specific to skills:

- **Another agent's paths.** A skill written for one agent hardcodes its layout, so a Cursor-native transcript path like
  `~/.cursor/projects/<slug>/agent-transcripts/` finds nothing here.
- **Delegation to skills that are not here.** A skill lifted out of a bundle hands work to its siblings; unless those
  are vendored too, the steps that call them are undefined.

Neither is grounds for rejection on its own, but the `vetted` line has to say so plainly: the skill lands in
`~/.agents/skills` and every agent loads it. `disable-model-invocation: true` in the frontmatter makes it
explicit-request-only, capping the blast radius of one that is not fully usable yet.

## Updating

`just skills check` reports which upstreams moved a skill's own bytes; unrelated commits in the same repo do not count.
`just skills sync --latest <name>` takes the new content and flips `vetted` to `PENDING`, keeping the old verdict
inline, so re-vet and write the new one by hand. Plain `just skills sync` re-copies the pinned commit, healing drift;
add `--dry-run` to report it and exit non-zero instead.

## Removing

Delete the source directory. The rendered copy in `~/.agents/skills/` survives, because `chezmoi apply` only ensures
targets still in the source state, so remove it by hand as well.
