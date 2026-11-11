---
name: file-pr
description: File a concise pull request. Use when the user asks to file, open, or create a PR.
---

# File PR

If `gh repo view <repo> --json viewerPermission` for the PR's target repo is `READ` or `TRIAGE`, the repo belongs to someone else: show the user the title and description and ask before you push or file.

If a PR for this branch already exists, push and leave its title and description alone, because the user may have edited them. Update only the credit lines.

Commit the changes that belong to this change with the `commit` skill. Leave any other uncommitted changes where they are and name them in your report. Do not stash or commit them.

Never push to the default branch unless the user asks. Before you push, list the branch's commits with `git log origin/<default>..HEAD`. If it lists commits from an unpushed local default branch, rebase them out with `git rebase --onto origin/<default> <default>`.

## Cross-model review

Before the push, run `autoreview` with no arguments. The wrapper on PATH reviews this branch against the default branch at P1. Exit 0 is clean, exit 1 means findings, and exit 2 means the review did not finish. Read `~/.agents/skills/autoreview/SKILL.md` only when the wrapper fails or you need another mode. Reach a clean exit, unless the user waived it for this change. The authoring model never reviews its own work: Claude-authored code keeps the Codex default engine, Codex-authored code runs `--engine claude`, and the reviewer stays the same for every cycle of one loop. Findings are advisory; verify each against the real code. Review feedback never grows the PR past its original goal: fix real shortcomings, decline the rest with a one-line reason. After two fix cycles without convergence, stop and report.

## Title and description

Follow the repo's title convention, and say what the change does rather than how: "cut websocket frame size by 70%+ with gzipping", not "negotiate permessage-deflate on the websocket".

Before you write the description, read `~/.agents/skills/technical-writing/SKILL.md` and `~/.agents/skills/unslop/SKILL.md`.

The user often reads the description after the PR merged without them. Write it so they understand the change in a minute, with these sections:

- **Why the change:** one sentence: the problem, and what works after the merge.
- **Things to note:** first `Door: one-way` or `Door: two-way`, with the reason in a few words. A two-way door is safe to revert. A one-way door is not, such as a data migration, deleted data, or a changed public contract. Then up to 3 bullets the user must not miss, such as a deliberate omission or a surprising decision.
- **Change outline:** the smallest visual that shows the shape of the change, each next to one short sentence. Use a `diff` block for a call tree, file tree, data shape, or pseudocode that already existed, a plain block for a new one, and Mermaid for flow between parts. Never a file-by-file changelog. Leave this section out when a visual would not make the change easier to understand.
- **Proof:** one line on how you proved the change. Mention a check only if you ran it. For a visual change, upload a screenshot or a short recording with the `file-upload` skill and embed it here.

End the description with these lines, in place of any attribution line the harness adds. Use the model names the harness and `autoreview` report. If a model name is unavailable, name the harness without guessing a model.

```
Created with <model> in <harness>. <Subagent models that wrote part of the change, if any.>
Reviewed with autoreview: <N> rounds with <reviewer model>. Verdict: <final verdict>.
```

Keep the verdict line even when the reviewer was not satisfied. When you push more commits to the PR, update the first line. Update the review line only when `autoreview` ran again.

Open a real PR, not a draft, so review bots run. Then watch it with the `babysit-pr` skill.
