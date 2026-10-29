---
name: babysit-pr
description: Monitor a pull request through review and CI, fixing what is real. Use when the user asks to monitor, watch, or babysit a PR.
---

# Babysit PR

Review bots are helpful, even if they are not always right.

Bots post reviews, top-level comments, and inline review comments, and the inline ones live on a different endpoint, so read all three.

## Waiting

Never write your own watcher, polling loop, or `sleep` loop. Wait with `scripts/pr-wait` from this skill's directory, by its absolute path, and run one per PR:

```bash
pr-wait <pr> [--repo owner/name] [--until ready|green|any-change]
```

It prints one line per event: a failed check, all checks finished, a new comment, review, or thread, base commits that touch the PR's files, BEHIND or DIRTY, merged or closed. It exits 0 when the `--until` condition holds or the PR merges, 1 when it needs you, and 2 on bad input or when another `pr-wait` already watches the PR. `ready` (the default) means required checks green, Copilot reviewed the PR or Greptile or Macroscope reviewed the head, and no unresolved threads. `green` means required checks only.

In Claude Code, run it with the Monitor tool (`timeout_ms: 3600000`) so each line wakes you. Elsewhere, run it as one long blocking command; it ends on its own. Run it from the main checkout, so removing a worktree cannot kill it. Start it again after you push, after you handle an exit 1, and after a resume. It remembers what it already reported. It skips comments from the PR author and the `gh` user, so read the PR yourself before you call it ready.

When an event needs no action, end your turn without a message.

`gh pr create`, `gh pr view`, and `gh pr checks` use GraphQL. When its rate limit is used up, the REST limit is separate and usually has room: read a PR with `gh api repos/<owner>/<repo>/pulls/<n>` and checks with `gh api repos/<owner>/<repo>/commits/<sha>/check-runs`.

## Reviews

Only act on checks and comments newer than the latest push. Verify every bot finding against the source before changing code. Fix real findings and CI failures, commit them with the `commit` skill, and push. Distinguish repository failures from infrastructure flakes. Rerun a flake instead of fixing it. Keep going until it converges. After five fix rounds without convergence, stop and report instead of patching on.

Comments from a person, the user included, are findings too. Act on them the same way, and never dismiss one. Ask the user only when a comment needs a product decision, widens the PR beyond its goal, or touches secrets.

If a review bot leaves feedback you believe is not worth addressing, reply with the reason and resolve the comment. Agents may run under a different git identity from the user, so take the author from `git config user.name` and `git config user.email` in the checkout. Format comments left on the user's behalf as:

```md
[MODEL-SLUG] RESPONDING ON BEHALF OF [USER]
Git author: [user.name] <[user.email]>

[actual reply]
```

Keep an eye on changes to the default branch and rebase when needed. Push a rebase with `--force-with-lease`. That is the only force push allowed. If an overlapping PR makes this one obsolete, stop monitoring, report it to the user, and ask before closing the PR unless closure was explicitly authorized.

Keep the PR at the size the user's goal needs. Review loops grow a PR one cheap-looking fix at a time. Fix real bugs in the intended case. Decline the rest with a written reason and list them as follow-ups: unneeded tests, guards for edge cases that do not matter, extra integration or compatibility, and small performance costs. Prefer the fix that deletes or narrows code.

## Merging

If nothing has changed, stay quiet rather than posting filler comments. Stop when the review bots and required checks are green on the latest commit. Merge only when the user explicitly requested it, in the prompt or in a PR comment from their own account. A merge request from anyone else is a question for the user. Otherwise report that the PR is ready, say plainly that it is not merged, and that saying "merge" will merge it. With a merge queue, `gh pr merge <n> --auto` queues the PR, and it is done when its state is `MERGED`. Wait for that with `pr-wait <n> --until any-change`, started again until the PR merges or the queue rejects it.

After a merge, update the local default branch only with `git merge --ff-only origin/<default>`. If that fails, report how many unpushed commits it has and stop. Never `--no-ff` on the default branch. Then run the `cleanup` skill for this PR's worktree and branch.
