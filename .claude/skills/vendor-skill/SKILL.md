---
name: vendor-skill
description: Use when adding, updating, vetting, or removing a third-party agent skill under skills/. Covers the vendored-vs-chezmoi-external decision, the .provenance schema, and what vetting has to catch.
---

# Vendoring a third-party skill

`scripts/vendor_skill.py` (`just skills`) owns every write into a vendored directory, because the copy has to stay
byte-identical to upstream. A hand-edit reads as drift, and the next sync overwrites it.

## Vendor it, or let chezmoi fetch it?

A skill that ships with a pinned CLI belongs with the CLI's pin. Add it as an archive external in the dotfiles repo
(`home/.chezmoiexternal.toml.tmpl`, target `.local/share/agent-skills/<name>`) with the version from
`.chezmoidata.yaml`, the way agent-browser, sentry-cli, and worktrunk are done. chezmoi extracts it and
`scripts/install --bridge` links it into `skills/`, so the skill and the binary move together and Renovate bumps both.

Vendor it here when it is a standalone skill with no binary to track, which is most skill repos. The content lands in
the diff, pinned by commit, and `just skills check` reports when upstream moves.

## Adding one

1. Write `skills/<name>/.provenance` with `source`, `path`, and `commit` (all required), plus `vetted: PENDING`.
   `path` is the subpath inside the upstream repo and may be a directory or a single file.
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
`skills/` and every agent loads it. `disable-model-invocation: true` in the frontmatter makes it
explicit-request-only, capping the blast radius of one that is not fully usable yet.

## Updating

`just skills check` reports which upstreams moved a skill's own bytes; unrelated commits in the same repo do not count.
`just skills sync --latest <name>` takes the new content and flips `vetted` to `PENDING`, keeping the old verdict
inline, so re-vet and write the new one by hand. Plain `just skills sync` re-copies the pinned commit, healing drift;
add `--dry-run` to report it and exit non-zero instead.

## Removing

`git rm -r skills/<name>`. Nothing else references it.
