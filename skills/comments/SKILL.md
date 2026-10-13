---
name: comments
description: Rules for writing code comments. Use when adding or editing a comment in any language, or when reviewing a diff that adds comments.
---

# Comments

Write for someone reading the repo at HEAD months from now, with no access to
this conversation, the PR, or the diff. A comment earns its place only when it
says something they cannot recover from the code.

Before writing one, try a better name, a smaller function, or a type. Comment
only when none of those can carry it. In config files there is nothing to
rename, so the bar is the sentence itself.

## Rules

- One idea per comment.

- Do not narrate history. "now", "previously", "no longer", "used to",
  "per PR #123": only one approach exists at HEAD.

  ```text
  # BAD:  We now intern types instead of cloning them.
  # GOOD: Interning avoids a clone on every lookup.
  ```

- Do not address the reviewer. A comment arguing your change is correct is
  written for whoever reads the PR, not whoever reads the file in a year.

- Do not log a decision. Why you picked an approach, what you rejected, what you
  tried first: that is the commit message. The exception is a constraint. If
  someone undoes it and nothing complains, it was load-bearing, so write it as
  the trap rather than the deliberation.

  ```text
  # BAD:  Chose a queue over a cron job after weighing both.
  # GOOD: A cron job double-fires when two deploys overlap.
  ```

- Say it once. Explain a fact at its definition; everywhere else points at it
  or stays silent. A doc file carries the pattern, the code carries the
  instance.

- Do not hardcode a value the code owns, or one taken from upstream; both go
  stale. Name the observable, not the number.

- Do not open with a restatement of the next line. The waste is usually the
  first clause of an otherwise useful comment, not the whole thing.

  ```text
  # BAD:  Close the connection first: the pool reuses sockets and will hand
  #       this one out again mid-write.
  # GOOD: The pool reuses sockets and will hand this one out again mid-write.
  ```

- No section banners where the language already groups. The exception is a
  long flat list where a comment is the only structure the syntax allows.

- Do not teach. The reader knows the language and the tools.

- No commented-out code. If it is already there, leave it.

## Before you finish

Re-read only the comments in your diff, in isolation from the code. Delete what
does not pass. A missing comment is cheaper than a misleading one. Judge the
comment, not its author.
