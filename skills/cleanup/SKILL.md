---
name: cleanup
description: Remove the worktrees, branches, containers, and background processes this session created, once its work is merged. Use when the user says "clean up" or asks whether the session is cleaned up at the end of a task.
---

# Cleanup

The user asking for cleanup is the authorization. Print what you will remove and what you will leave, with the reason
for each one left, then start removing in the same turn. Do not wait for a reply; the user interrupts if the list is
wrong.

## What belongs to this session

Only what this session created or worked in, judged from the conversation: worktrees and branches it made, test stacks
and containers it started, and background processes it launched. Anything you cannot tie to this session stays, even
when it looks abandoned. After a context compaction, if the summary does not name a worktree, leave it.

## When a worktree is safe to remove

Run `git fetch --prune` first. A worktree and its branch are safe to remove when both hold:

- `git -C <path> status --porcelain` prints nothing.
- The branch's work is on the default branch: `gh pr view <branch> --json state` says `MERGED`, or
  `git branch --merged origin/<default>` lists it.

Uncommitted changes, an open PR, or commits that never reached a merged PR block that one worktree. Skip it, carry on
with the rest, and say why in the report. Never use a force flag to get past a block.

## Remove

Run from the main checkout. If your shell sits inside a worktree you are removing, move out of it first.

With worktrunk (`wt` on PATH), remove all safe worktrees in one call:

```bash
wt remove --foreground --reap <branch>...
```

It runs the project's pre-remove hooks, which tear down test stacks, and kills processes running inside each worktree.
It deletes a branch only when the branch is merged. If it keeps a branch whose PR `gh` reports as `MERGED`, the PR was
squash-merged and `git branch -D <branch>` is safe.

Without worktrunk, stop the session's containers and processes for each worktree, then run
`git worktree remove <path>` and `git branch -d <branch>`. The same squash-merge rule allows `-D`.

Then finish the rest:

- Delete the remote branch with `git push origin --delete <branch>` if its PR merged and the branch still exists.
- Stop any container or process the session started outside a worktree.
- Run `git worktree prune`.
- If the main checkout is clean, switch it to the default branch and run `git pull --ff-only`.

## Report

Show `git worktree list` output, then list what you removed, what you left and why, and the main checkout's branch and
whether it is in sync with origin.
