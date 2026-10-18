---
name: handoff
description: End an analysis session by filing the tracking issue, creating the worktree, and printing the command that starts a fresh implementation session. Invoked by the user as /handoff or $handoff.
disable-model-invocation: true
---

# Handoff

A long analysis makes a slow, noisy implementation session. Hand the work to a fresh one instead of starting it here. Treat any argument as steering for the issue.

1. **File the issue.** Put the whole plan in the body: the problem, the decision and why, the steps, what is out of scope, and how to verify it. The fresh session reads only the issue, so leave nothing behind in the conversation. Follow the repo's issue conventions and the `technical-writing` skill. If an issue already tracks the work, add the plan to it as a comment.
2. **Create the worktree** with the `worktrunk` skill, named after the issue: `wt switch --create <type>/GH-<n>-<slug> --no-cd`.
3. **Print one command** that starts the fresh session in the agent you are running in, then stop:

   ```bash
   cd <worktree path> && claude "Implement <owner>/<repo>#<n>. Read the issue first."
   ```

Do not start implementing or edit files in this session.
