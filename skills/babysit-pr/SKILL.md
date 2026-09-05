---
name: babysit-pr
description: Monitor a pull request through review and CI, fixing what is real. Use when the user asks to monitor, watch, or babysit a PR.
---

# Babysit PR

Review bots are helpful, even if they are not always right.

If your harness offers tools to monitor a PR, use them so you can respond when comments arrive. Otherwise poll with `gh`. `gh pr checks <pr> --watch` blocks until CI finishes. Bots post reviews, top-level comments, and inline review comments. `gh pr view <pr> --json reviews,comments` returns the first two. `gh api repos/{owner}/{repo}/pulls/<pr>/comments` returns the inline ones.

Only act on checks and comments newer than the latest push. Verify every bot finding against the source before changing code. Fix real findings and CI failures, commit them with the `commit` skill, and push. Distinguish repository failures from infrastructure flakes. Rerun a flake instead of fixing it. After two fix rounds without convergence, stop and report instead of patching on.

Comments from a person are for the user to weigh. Surface them, do not argue with them.

If a review bot leaves feedback you believe is not worth addressing, reply with the reason and resolve the comment. Format comments left on the user's behalf as:

```md
[MODEL-SLUG] RESPONDING ON BEHALF OF [USER]

[actual reply]
```

Keep an eye on changes to the default branch and rebase when needed. Push a rebase with `--force-with-lease`. That is the only force push allowed. If an overlapping PR makes this one obsolete, stop monitoring, report it to the user, and ask before closing the PR unless closure was explicitly authorized.

Do not let review feedback expand the PR beyond the user's original goal. Address real shortcomings, but avoid scope creep.

If nothing has changed, stay quiet rather than posting filler comments. Stop when the review bots and required checks are green on the latest commit. Merge only when the user explicitly requested it. Otherwise report that the PR is ready.
