---
name: ship
description: Push the current branch, file a PR, then babysit it through CI and review bots until it is green. Use when the user wants committed work shipped for review.
disable-model-invocation: true
---

# Ship

Run the `file-pr` skill, then the `babysit-pr` skill on the PR it filed or reused. Treat any argument as steering for the PR title and description.

Every invocation is the user running `/ship` themselves. That is the authorization to push, to fix real findings, and to reply to bots on their behalf. Do not stop to ask. The user kicks off ship, walks away, and comes back to a PR that is green or a report that says why it is not. Merging still needs an explicit request.
