---
name: ship
description: Push the current branch, open (or reuse) a GitHub PR, wait for CI and any automated code reviewers (Copilot, CodeRabbit, Greptile, or any review bot), then critically triage every bot comment and CI failure into a report — without making code changes. Use when you want to ship work for review and get a skeptical assessment of the feedback before deciding what to fix.
disable-model-invocation: true
---

# Ship: push → PR → CI + bot reviews → skeptical triage

Optional argument (branch name / PR title override): $ARGUMENTS

This skill takes committed work, gets it in front of GitHub's CI and whatever
automated code reviewers are configured on the repo, then hands you back a
*judgement* — not a list of orders. Automated reviewers (Copilot, CodeRabbit,
Greptile, Cursor BugBot, AI reviewers, …) are useful but every one of them
produces noise: they over-engineer, invent abstractions, raise false positives,
and nitpick style as if it were correctness — each with its own bias. The whole
point of this skill is that **a human decides what to fix**. You push, wait,
and then argue with the bots on the user's behalf so they only have to read a
clean verdict. This is deliberately reviewer-agnostic: new review bots are
picked up automatically, never silently dropped.

Run every command yourself (`git`, `gh`). Do not rely on shell preprocessing —
this skill is shared across agents. **Never edit code in this skill.** It ends
with a report and a full stop.

## Phase 0 — Preflight and state detection

1. Confirm tooling: `gh auth status` succeeds and `git remote get-url origin`
   points at GitHub. If not, stop and tell the user what's missing.
2. Capture state:
   - Default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
   - Current branch: `git branch --show-current`
   - Working tree: `git status --porcelain`
   - Commits vs origin: `git status -sb` / `git log --oneline @{u}.. 2>/dev/null`
3. Decide based on state — this is the "detect & handle each case" contract:

   - **Uncommitted changes present** (anything in `git status --porcelain`):
     **stop here.** Report the dirty files and tell the user to commit first
     (suggest the `commit` skill). Do not auto-commit and do not stash —
     silently absorbing uncommitted work into a PR is exactly the kind of
     surprise that erodes trust.

   - **On the default branch** (e.g. `main`/`master`) with commits not on
     `origin/<default>`: create a feature branch so you never push straight to
     the protected branch. Derive a slug from the most recent commit subject
     (strip any `type:`/`type(scope):` prefix, lowercase, non-alphanumeric →
     `-`, collapse repeats, trim, cap ~50 chars); if `$ARGUMENTS` looks like a
     branch name, prefer it. Then:
     ```
     git switch -c <branch>
     git branch -f <default> origin/<default>   # keep local default clean
     ```
     State plainly that you moved the commits onto `<branch>` and reset local
     `<default>` back to its remote. `origin/<default>` is never touched.

   - **On the default branch with nothing ahead of origin**: there is nothing
     to ship. Stop and say so.

   - **On a feature branch with commits**: proceed as-is.

## Phase 1 — Push

`git push -u origin HEAD`. If the remote rejected it (non-fast-forward,
protected branch, etc.), stop and report the exact error — do not force-push.

## Phase 2 — Open or reuse the PR

Check first: `gh pr view --json number,url,state,isDraft`.

- If an **open** PR already exists for this branch, reuse it (the push above
  already updated it). Note the PR number/URL.
- Otherwise create one against the default branch:
  `gh pr create --fill --base <default>` (use `$ARGUMENTS` as the title if it
  reads like a title rather than a branch name). `--fill` derives title/body
  from the commits, which matches how the user already writes messages.

Record `<pr>` (number) and the PR URL for the report.

## Phase 3 — Wait for CI and automated reviewers

Both are asynchronous and slow, and you don't know in advance which review bots
this repo has or how many will post. Poll for **up to 20 minutes total** (some
test suites genuinely take that long) on roughly a 30-second cadence. Each tick:

- CI: `gh pr checks <pr> --json name,state,bucket,link` (or plain
  `gh pr checks <pr>` if JSON is unsupported). Track pending vs done.
- Reviews/comments, across all three surfaces a bot might use — a formal
  *review*, inline *review comments*, or a top-level *issue comment*:
  - `gh pr view <pr> --json reviews,comments`
  - `gh api repos/{owner}/{repo}/pulls/<pr>/comments` (inline review comments)
  - `gh api repos/{owner}/{repo}/issues/<pr>/comments` (top-level comments)

**Identify bot reviewers generically — do not hardcode one vendor.** Treat an
author as an automated reviewer if any of these hold:
- the API reports it as a bot: `user.type == "Bot"`, or the login ends in
  `[bot]`, or `author_association` is `NONE`/`BOT` for a clearly machine
  account;
- the login matches a known reviewer (case-insensitive substring): `copilot`,
  `coderabbit`, `greptile`, `bugbot`, `cursor`, `sourcery`, `ellipsis`,
  `codeball`, `qodo`, `bito`, `sweep`, `devin`, `claude`, `gemini-code` — treat
  this as a non-exhaustive hint list, not a filter; an unrecognized bot login
  still counts as a bot via the first rule.

Everything else — real teammates — is a **human reviewer**: collect it, but it
is *not* subject to skeptical triage (see Phase 4).

Give the user a brief progress line every few ticks (e.g. "CI 3/5 done;
CodeRabbit posted, Copilot pending") so a 20-minute wait isn't a silent void.

**Exit the wait when** CI has finished (every check success or failure, none
pending) **and** bot review activity has stabilized — at least one bot review
is present and no *new* bot review or bot comment has appeared for ~2
consecutive ticks (so multiple reviewers that post at different times all get
captured). Also stop early if CI has finished and **no** bot review has
appeared within ~5 minutes after that: many repos simply have no review bot, so
don't burn the full 20 minutes waiting for one that will never come. Hard cap
at 20 minutes regardless. On timeout, do not fail: continue to the report with
whatever arrived, and clearly mark what was still pending (e.g. "CI still
running: e2e", "Greptile review never posted within 20 min").

## Phase 4 — Critically assess each comment

This is the part that earns its keep.

**Human review comments are not triaged.** If a real person left review
feedback, surface it verbatim (summarized if long) in its own section and defer
to the user — do not bucket it, argue with it, or "Reject" it. A human chose to
say it; the user can weigh it themselves. Skepticism is for the bots.

For **every bot comment**, read the actual code at the referenced `file:line`
before judging — automated reviewers frequently comment on things that are
fine, misread context, or propose abstractions heavier than the problem.
Default to skepticism, not deference. Different bots fail differently (Copilot
over-abstracts; verbose reviewers bury one real issue under ten nits) — judge
the comment on its merits, not its source, and apply the same bar to all of
them.

Classify each bot comment into exactly one bucket:

- **Fix** — a real defect: incorrect logic, a genuine bug, a security or data
  issue, a crash, or maintainability harm that a reviewer would reasonably
  block on. These are worth the user's time.
- **Optional** — a legitimate but discretionary preference: minor naming,
  micro-style, a defensible-either-way choice. Note it, don't push it.
- **Reject** — wrong, redundant, based on a misread, contradicts this repo's
  established conventions, or is over-engineering (adding layers/abstraction/
  config for a hypothetical that isn't in scope). Say *why* in one line so the
  user can sanity-check your reasoning rather than trust it blindly.

Be specific and brief per item: `path:line` · which bot · what it wants (one
phrase) · verdict · one-line reason. Where the suggestion is wrong, a crisp
counter ("the null case can't occur here — `x` is set on line 12") is more
valuable than the original comment.

Also fold in CI: for each failing check, name it and include the smallest
useful log/test-failure snippet (`gh run view <run-id> --log-failed` or the
check's `link`). A red test is almost always a real Fix.

## Phase 5 — Report, then stop

Output exactly this structure, then **stop and wait** — do not implement
anything. The user reviews the verdict and tells you what to action next.

```
# Ship report — <branch> → PR #<n>

PR: <url>
Reviewers seen: <e.g. Copilot, CodeRabbit · or "none posted">

## CI
- <check>: <pass/fail/pending> [<one-line note or failure snippet>]
...
<"All green" / "N failing" / "still running: …">

## Bot review — triage
### 🔴 Fix (N)
- <file:line> · <bot> — <what> → <why it's real>
### 🟡 Optional (N)
- <file:line> · <bot> — <what> → <why discretionary>
### ⚪ Reject (N)
- <file:line> · <bot> — <what> → <why it's wrong / over-engineered / off-convention>

## Human review (if any) — not triaged, for your call
- <reviewer> on <file:line>: <comment, summarized> — <verdict: approved / changes requested / commented>

## Recommendation
<2–4 sentences: what genuinely needs doing before merge, what to skip, and
anything still pending (CI / a reviewer) that may change this picture.>

—— Stopping here. Tell me which items to fix and I'll proceed. ——
```

Omit the Human review section entirely if no person commented. If nothing needs
fixing and CI is green, say so plainly — "ready to merge, no substantive
feedback" is a perfectly good outcome and shouldn't be padded. If multiple bots
reviewed and one was consistently noise while another caught a real issue, one
line on that is genuinely useful — it's how the user decides which reviewers to
keep on the infra.
