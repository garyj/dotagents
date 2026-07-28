---
name: agent-rules
description: Rubric for what belongs in an AGENTS.md, CLAUDE.md, or .rules file. Use when writing one, proposing an addition to one, or auditing an existing one.
---

# Agent rules files

Every rule is read at the start of every session and competes with every other
rule for attention. A file that documents the repo makes the traps buried in it
less likely to be followed. Write traps to avoid, not maps to follow.

## A rule earns its place only if all three hold

1. **Non-obvious.** Someone already familiar with the codebase would still get
   it wrong without the rule.
2. **Repeatedly encountered.** It has come up more than once. Several hits in
   one session counts; a single mistake does not.
3. **Specific enough to act on.** A concrete instruction, not a principle.

State the trap, not just the instruction. "Do not use the shared client here"
gets ignored; "the shared client holds one connection, so two of these deadlock"
does not.

## Cut on sight

- Directory layouts, module maps, data flow, key types. These go stale, and the
  agent can read the code.
- Command inventories, and anything a listing or `--help` already answers.
- Rules that belong to one subdirectory. Put them in that directory's own file.
- Anything a linter, a hook, or a type already enforces.

## Auditing a file

Take one rule at a time, in isolation from the rest of the file. Ask which of
the three tests it fails, and cut on the first failure rather than weighing the
rule's merits. Report what went and what stayed.

## Adding a rule

No drive-by additions. When a session turns up something that would have helped,
propose it in your reply, with the evidence that it came up more than once. Do
not edit the rules file as a side effect of unrelated work.
