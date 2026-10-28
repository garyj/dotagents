---
name: cleanup
description: Use when the user says `clean up`, or a PR this session filed reaches `MERGED`, to remove the worktrees, branches, containers, and background processes this session created once its work is merged.
---

# Cleanup

- The user asking for cleanup is the authorization, and so is a PR this session filed reaching `MERGED`.
- Print what you will remove and what you will leave, with the reason for each one left, then start removing in the
  same turn.
- Do not wait for a reply; the user interrupts if the list is wrong.

## What belongs to this session

Only what this session created or worked in, judged from the conversation: worktrees and branches it made, test stacks
and containers it started, and background processes it launched. Anything you cannot tie to this session stays, even
when it looks abandoned. After a context compaction, if the summary does not name a worktree, leave it. Do not use
`wt step prune`; it removes every merged worktree, not only this session's.

## Remove

Use worktrunk for the checks and the removal. Read the `worktrunk` skill's `reference/list.md` (JSON output) and
`reference/remove.md` for the current commands and fields.

Run from the main checkout. Run `git fetch --prune` first so worktrunk compares against the current default branch.

A worktree is safe to remove when all of these hold:

- Its working tree is clean.
- Its work is on the default branch.
- Its PR is not open. If worktrunk cannot tell whether a PR is open, treat it as open.

Skip any other worktree, carry on with the rest, and say why in the report. Never use a force flag (`-f`, `-D`) to get
past a block. Remove the safe worktrees in the foreground, and reap their processes so the project's pre-remove
hooks and process cleanup finish before you report. If worktrunk keeps a branch as unmerged but `gh pr view <branch>
--json state` reports `MERGED`, the PR was squash-merged and `git branch -D <branch>` is safe.

Then:

- Delete the remote branch with `git push origin --delete <branch>` if its PR merged and the branch still exists.
- Stop any container or process the session started outside a worktree.
- If the main checkout is clean, switch it to the default branch and run `git pull --ff-only`.

## Report

Show `wt list` output, then list what you removed, what you left and why, and the main checkout's branch and whether it
is in sync with origin.
