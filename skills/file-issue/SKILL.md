---
name: file-issue
description: File a GitHub issue that a coding agent can fix unattended. Use when the user asks to file, open, or create an issue.
---

# File Issue

Another agent will fix this issue with `full-send`. It reads only the issue, once, at the start, so put everything it needs from this conversation in the body.

If `gh repo view <repo> --json viewerPermission` is `READ` or `TRIAGE`, the repo belongs to someone else: show the user the draft and ask before you file it.

Search open and closed issues first. Comment on an open match instead of filing. Link a closed match from the new issue.

The body needs:

- **Problem:** the evidence you saw yourself, such as output, a traceback, or file paths, with the date.
- **Expected:** the behavior, not the fix, unless the user decided the fix.
- **Proof:** numbered steps that fail now and pass after the fix. Reproduce first so you know they fail.
- **Out of scope:** nearby things the agent must not change.
- **Unknown:** open questions marked ❓, including a missing Proof.

Write the title in the repo's PR title style, because the agent's PR follows it. End the body with `Filed with <model> in <harness> on behalf of <user>.`
