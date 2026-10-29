---
name: file-pr
description: File a concise pull request. Use when the user asks to file, open, or create a PR.
---

# File PR

Before filing, check whether a PR for this branch already exists. If one does, push and leave its title and description alone. The user may have edited them.

If the working tree has uncommitted changes, stop and say so. Do not stash them and do not commit them. Point the user at the `commit` skill.

If you are on the default branch, move the commits to a new branch and reset the local default branch to its remote. Never push to the default branch unless the user asks for it.

Review the diff locally against the remote default branch to make sure its contents match the goal. List the branch's commits with `git log origin/<default>..HEAD`. If any commit is not this change, the local default branch is ahead of its remote and the branch inherited its commits. Rebase them out with `git rebase --onto origin/<default> <default>` before pushing.

## Cross-model review

Before the push, run `autoreview` (wrapper on PATH; skill at `~/.agents/skills/autoreview/SKILL.md`) and reach a clean exit, unless the user waived it for this change. The authoring model never reviews its own work: Claude-authored code keeps the Codex default engine, Codex-authored code runs `--engine claude`, and the reviewer stays the same for every cycle of one loop. Findings are advisory; verify each against the real code. Review feedback never grows the PR past its original goal: fix real shortcomings, decline the rest with a one-line reason. After two fix cycles without convergence, stop and report.

## Title and description

PR titles usually become commit messages, so follow the repository's title conventions. Look at recently merged PRs and Git history for examples. Prefer a concise, human-readable title that explains why the change matters:

BAD
> perf(server): negotiate permessage-deflate on the websocket

GOOD
> perf(server): cut websocket frame size by 70%+ with gzipping

Open the description with a simple explanation of the problem based on the user's original prompt, then briefly explain the solution. Do not lead with an inventory of the files, functions, and entry points touched.

Mention a check only if you ran it. Never write a test plan you did not do. Add one short line that says how you proved the change.

Never use `gh pr create --fill`.

Push the branch, then open a real PR rather than a draft so review bots run. If the user also asked to babysit it, continue with the `babysit-pr` skill.
