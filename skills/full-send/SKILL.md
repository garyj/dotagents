---
name: full-send
description: Use when the user says "full send".
---

# Full Send

The user said "full send" because they will not watch this run. You own the work from its current state to a merged PR, and your updates go unread until long after you stop. If the user did not clearly ask for "full send", do not assume this autonomy.

"Full send" grants permission to:

- Commit and push this task's branch, and force-push it with `--force-with-lease` after a rebase.
- Merge the PR once the merge gate passes.
- Use any test method Proof needs without asking first: browser automation, running the app or a dev server, screenshots. This replaces an ask-first rule in a project file for this task only. Rules that name the command, fixture, or check to use still apply.

It grants nothing listed under "When to stop and ask", and it does not bypass a harness approval prompt.

## Steps

1. **Ask first, once.** Read the issue or request and its comments, then print the plan: the change, what is out of scope, and how you will prove it. Find the proof method in the repo before you print the plan: its AGENTS.md, test setup, verification skills, or a way to run the app. If none can prove this change, say so and ask how the user expects it to be verified, and recommend `full-stop` or a watched run in place of an unattended merge. Ask every question whose answer would change what the PR looks like, in one round, with the harness's question tool: `AskUserQuestion` in Claude Code, `request_user_input` in Codex, or the equivalent in your harness. Put the plain reading of the request first as the recommended answer: no guards, edge cases, or extras it did not ask for. If the harness has no question tool, ask in a normal message and end the turn before writing code. When the last answer is in, or nothing was unclear, print this line on its own as a heading, then start: `🚀 FULL SEND: no more questions, starting now` (`FULL STOP` under `full-stop`). Ask nothing else before it. The user is at the keyboard for this step and gone after the banner.
2. **Branch.** Create a worktree with the `worktrunk` skill, named by the branch rules in your instructions. Never work on the default branch.
3. **Finish the change.** Make the smallest change that does what was asked. Fix the case that happened, not every case that could.
4. **Prove it.** See "Proof".
5. **Commit and file** with the `commit` and `file-pr` skills. `file-pr` runs `autoreview` and adds the proof line.
6. **Babysit** with the `babysit-pr` skill. Get proof for each fix before you push it.
7. **Merge** when the merge gate passes, with the method the repo uses: its AGENTS.md first, then recent merged PRs. With a merge queue or auto-merge, stay until GitHub reports `MERGED`. Never use `--admin` or another bypass.
8. **Clean up** with the `cleanup` skill.
9. **Report.** See "Report".

Stay active from step 2 to step 9. If you end your turn while checks or bots are pending, the work stops, because nobody will prompt you again. Wait with `pr-wait` from `babysit-pr`, so something wakes you when the PR changes.

## Proof

Proof is evidence you saw yourself in this session, and it meets the verification rules in your instructions and the repo's AGENTS.md. Use the most direct proof the change allows:

- Reproduce the original failure, apply the fix, then watch the same reproduction pass.
- For UI and runtime behavior, run the app and look at the change. Green mocked tests do not prove that the user experience works.
- Add one focused test that fails without the fix, when the behavior has none and the repo has a test setup.

If a change still cannot be proved after step 1, do not merge it. Finish the way `full-stop` does: leave the PR open and unmerged, and say in the report what is not proved.

## Merge gate

All of these are true on the latest commit:

- Your proof covers every change in the diff.
- Required checks are green.
- Review bots have finished, and each finding is fixed or declined with a written reason.
- No human review still requests changes.
- The branch is up to date with the default branch, and GitHub reports it as mergeable.

## When to stop and ask

After step 1, ask only when you cannot continue alone:

- The merge gate cannot pass for a reason other than proof, and you cannot fix that yourself.
- The next step is outside the grant: deleting data, production, deploys, secrets, changes outside the repo, closing a PR, or force-pushing any other branch.
- A new ambiguity would change the result.
- Another PR makes this one obsolete.

Decide everything else by the plain reading of the request, and list each decision in the report.

A question in a normal message goes unseen, and the run looks done. Ask with the question tool from step 1, and put all the context in the question: the PR link, what blocks you, and the options with your recommendation first. If there is no question tool, or it returns no answer, leave the PR open and unmerged, and start your final message with the question.

## Report

Your final message gives the PR link, the merge commit, your proof, what `cleanup` removed, and each decision you made for the user.
