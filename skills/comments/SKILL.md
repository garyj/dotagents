---
name: comments
description: Rules for writing code comments. Use when adding or editing a comment in any language, or when reviewing a diff that adds comments.
---

# Comments

Write for someone reading the repo at HEAD months from now, with no access to
this conversation, the pull request, or the diff. Only one approach exists at
HEAD: the one in the file.

## The test

Before writing a comment, ask: **does this say something the reader cannot
recover from the code?** If names, types or structure already carry it, don't
write it. If the name fails to carry it, fix the name.

## Never

**Narrate history.** "now", "previously", "no longer", "used to", "the new
approach", "changed from", "per PR #123", "as discussed". These are meaningless
at HEAD.

```python
# BAD:  We now intern types instead of cloning them.
# GOOD: Interning avoids a clone on every lookup.
```

**Address the reviewer.** A comment arguing your change is correct is aimed at
whoever reads the PR, not whoever reads the file in a year.

```python
# BAD:  This correctly handles the overload case from the bug report.
# GOOD: Overloads match by arity before parameter types, so a partial-arity
#       call cannot select the wrong candidate.
```

**Log a decision.** Why you picked an approach, what you rejected, what you
tried first. That goes in the commit message, attached to the diff and
searchable, where it stays accurate because it describes a moment in time.

**Restate the next line.** `# Increment the counter` above `count += 1`. Delete
on sight.

**Add section banners.** `# ----- helpers -----`, `# ==== TYPES ====`.

**Teach.** The reader knows the language. Explaining what a systemd unit is, or
what semantic search does, is not a comment.

**Hedge.** "some cases", "various reasons", "handles edge cases", "etc." Name
them or drop the sentence.

## When a comment is right

Reach for one only after trying, in order: a better name, a smaller function, a
type. If none can carry the meaning, comment. Good subjects:

- A constraint the code cannot state: an upstream bug workaround (link the
  issue), a required ordering, a non-obvious coupling.
- A consequence that lives elsewhere: "callers rely on this being sorted",
  "changing this invalidates the cache key".
- Why the obvious alternative is wrong, stated as a property of the code rather
  than as a story about your reasoning.

## Shape

One line. If it needs a paragraph it is documentation: commit message, PR body,
or a doc file. Say it once, in one file, and let other sites stand on their own.

## Before you finish

Re-read **only the comments in your diff**, in isolation from the code. For
each: does it pass the test above? Does it reference the conversation, the
change, or the reviewer? Would someone without the diff understand it?

Delete what fails. A missing comment is cheaper than a misleading one. Leave
comments you did not write alone unless they break these rules or you can show
they are false.
