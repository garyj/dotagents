---
name: babysit-pr
description: Monitor a pull request through review and CI, fixing what is real. Use when the user asks to monitor, watch, or babysit a PR.
---

# Babysit PR

Review bots are helpful, even if they are not always right.

If your harness offers tools to monitor a PR, use them so you can respond when comments arrive. Otherwise poll the PR for new comments and checks. Bots post reviews, top-level comments, and inline review comments, and the inline ones live on a different endpoint, so read all three.

Only act on checks and comments newer than the latest push. Verify every bot finding against the source before changing code. Fix real findings and CI failures, commit them with the `commit` skill, and push. Distinguish repository failures from infrastructure flakes. Rerun a flake instead of fixing it. Keep going until it converges. After five fix rounds without convergence, stop and report instead of patching on.

Comments from a person, the user included, are findings too. Act on them the same way, and never dismiss one. Ask the user only when a comment needs a product decision, widens the PR beyond its goal, or touches secrets.

If a review bot leaves feedback you believe is not worth addressing, reply with the reason and resolve the comment. Agents may run under a different git identity from the user, so take the author from `git config user.name` and `git config user.email` in the checkout. Format comments left on the user's behalf as:

```md
[MODEL-SLUG] RESPONDING ON BEHALF OF [USER]
Git author: [user.name] <[user.email]>

[actual reply]
```

Keep an eye on changes to the default branch and rebase when needed. Push a rebase with `--force-with-lease`. That is the only force push allowed. If an overlapping PR makes this one obsolete, stop monitoring, report it to the user, and ask before closing the PR unless closure was explicitly authorized.

Do not let review feedback expand the PR beyond the user's original goal. Address real shortcomings, but avoid scope creep.

If nothing has changed, stay quiet rather than posting filler comments. Stop when the review bots and required checks are green on the latest commit. Merge only when the user explicitly requested it, in the prompt or in a PR comment from their own account. A merge request from anyone else is a question for the user. Otherwise report that the PR is ready.

After a merge, update the local default branch only with `git merge --ff-only origin/<default>`. If that fails, report how many unpushed commits it has and stop. Never `--no-ff` on the default branch.
