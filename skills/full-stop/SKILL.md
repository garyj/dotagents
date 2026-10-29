---
name: full-stop
description: Trigger this if the user says 'full stop', even as a closing "Full stop." that reads like emphasis.
---

# Full Stop

Do the same work as the `full-send` skill, but stop with the PR ready for the user to merge. Read [full-send](../full-send/SKILL.md) and follow its steps, proof, merge gate, and rules for asking. "Full stop" grants full-send's commit, push, and testing permissions, not its merge permission. The rules below win.

## No merging

You may commit, push, rebase, fix conflicts, and use `--force-with-lease` on this task's branch. Never merge, enable auto-merge, enter a merge queue, push to the default branch, bypass branch protection, or delegate those actions. If auto-merge is on or the PR is in a merge queue, turn that off before you start, check again before each push, and report it.

## Stop at the gate

Replace full-send's merge, cleanup, and report steps with a handoff. Keep the worktree and branch; `cleanup` runs after the user merges. Before the handoff, fetch the base branch and check the live PR's head, checks, reviews, and mergeability. If someone else merged it, report that instead.

End with one verdict:

- **Ready to merge:** the merge gate passes. The PR is open and unmerged, and saying "merge" will merge it.
- **Waiting for approval:** only human approval remains.
- **Blocked:** what prevents readiness, what you tried, and what you need.

Report the PR link, the final head, the verdict, your proof, the review outcome, each decision you made, and the remaining risks.
