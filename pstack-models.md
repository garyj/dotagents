# pstack model configuration. Read ONLY the section for the harness you are running in; ignore the other.
# One line per role. Delete a line to fall back to the skill default.
# `inherit-parent` or `auto` runs on the parent chat model with the subagent `model` omitted.
# Alias entries in panel lists count toward the number of agents.
# budget: medium (high), with per-role exceptions
# Hand-merged from two /setup-pstack runs. Re-running /setup-pstack overwrites both sections.

## Claude Code
# Effort targets: high by default, xhigh for hardest tasks.
# Use medium for feature, refactoring; how explorer; reflect tooling; and swarm workers.
# Model aliases do not set effort; apply these targets through supported effort controls.
# Without per-invocation effort, agent definitions must set it or the session/default effort applies.
feature, refactoring: opus
bug-fix: opus
perf-issue: opus
hillclimb: opus
judgment and prose: fable
hardest tasks: fable
how explorer: sonnet
how explainer: fable
why investigators: opus
why synthesizer: fable
reflect tooling: sonnet
reflect judgment, divergent, synthesizer: fable
arena runners: opus, sonnet
arena cross-judge pool: opus, sonnet
swarm workers: opus
architect runners: opus, sonnet
interrogate reviewers: opus, sonnet

## Codex
# Pass reasoning_effort="high" separately for every configured real model unless an exception below applies.
# Pass reasoning_effort="medium" for how explorer, reflect tooling, and mechanical swarm workers.
# Pass reasoning_effort="xhigh" for hardest tasks.
feature, refactoring: gpt-6.1-sol
bug-fix: gpt-6.1-sol
perf-issue: gpt-6.1-sol
hillclimb: gpt-6.1-sol
judgment and prose: gpt-6-astra
hardest tasks: gpt-6-astra
how explorer: gpt-6.1-sol
how explainer: gpt-6-astra
why investigators: gpt-6.1-sol
why synthesizer: gpt-6-astra
reflect tooling: gpt-6.1-sol
reflect judgment, divergent, synthesizer: gpt-6-astra
arena runners: gpt-6.1-sol, gpt-6-astra
arena cross-judge pool: gpt-6.1-sol, gpt-6-astra
swarm workers: gpt-6.1-sol
architect runners: gpt-6.1-sol, gpt-6-astra
interrogate reviewers: gpt-6.1-sol, gpt-6-astra
