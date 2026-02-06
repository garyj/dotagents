---
name: commit
description: Create well-formatted commits with conventional commit format and emoji. Use when committing code changes, staging files, or creating atomic git commits.
---

# Smart Git Commit

Create well-formatted commit: $ARGUMENTS

## Current Repository State

- Git status: !`git status --porcelain`
- Current branch: !`git branch --show-current`
- Staged changes: !`git diff --cached --stat`
- Unstaged changes: !`git diff --stat`
- Recent commits: !`git log --oneline -5`

**Note**: If the branch name contains a Jira issue (e.g., ABC-123) or GitHub issue (e.g., GH-456), automatically include it in the commit message.

## What This Command Does

1. Unless specified with --no-verify, automatically runs pre-commit checks:
2. Checks the current branch name and extracts any Jira (ABC-123) or GitHub (GH-456) issue references
3. Checks which files are staged with git status
4. If 0 files are staged, automatically adds all modified and new files with git add
5. Performs a git diff to understand what changes are being committed
6. Analyzes the diff to determine if multiple distinct logical changes are present
7. If multiple distinct changes are detected, suggests breaking the commit into multiple smaller commits
8. For each commit (or the single commit if not split), creates a commit message including any detected issue references

## Branch Naming for Issue Linking

When working on a branch named with an issue reference, the commit message will automatically include it:

- **Jira issues**: Branch names like `feature/ABC-123-add-auth` or `fix/PROJ-456-memory-leak` will extract `ABC-123` or `PROJ-456`
- **GitHub issues**: Branch names like `feature/GH-789-add-validation` will extract `GH-789`
- **Format in commit**: Issue references are appended to the commit message (e.g., `feat: add user authentication [ABC-123]` or `fix: resolve memory leak (GH-789)`)

## Best Practices for Commits

- **Verify before committing**: Ensure code is linted, builds correctly, and documentation is updated
- **Atomic commits**: Each commit should contain related changes that serve a single purpose
- **Split large changes**: If changes touch multiple concerns, split them into separate commits
- **Conventional commit format**: Use the format <type>: <description> where type is one of:
  - feat: A new feature
  - fix: A bug fix
  - docs: Documentation changes
  - style: Code style changes (formatting, etc)
  - refactor: Code changes that neither fix bugs nor add features
  - perf: Performance improvements
  - test: Adding or fixing tests
  - chore: Changes to the build process, tools, etc.
  - build: Changes that affect the build system or external dependencies
  - ci: Changes to CI configuration files and scripts
  - infra: Changes related to deployment infra such as AWS, Render, Digital Ocean, etc.
  - dev: Developer experience improvements

## Guidelines for Splitting Commits

When analyzing the diff, consider splitting commits based on these criteria:

1. **Different concerns**: Changes to unrelated parts of the codebase
2. **Different types of changes**: Mixing features, fixes, refactoring, etc.
3. **File patterns**: Changes to different types of files (e.g., source code vs documentation)
4. **Logical grouping**: Changes that would be easier to understand or review separately
5. **Size**: Very large changes that would be clearer if broken down

## Examples

Good commit messages:

- feat: add user authentication system
- fix: resolve memory leak in rendering process
- docs: update API documentation with new endpoints
- refactor: simplify error handling logic in parser
- fix: resolve linter warnings in component files
- refactor: simplify error handling logic in parser (GH-101)
- chore: improve developer tooling setup process
- feat: implement business logic for transaction validation
- fix: address minor styling inconsistency in header
- fix: patch critical security vulnerability in auth flow
- style: reorganize component structure for better readability
- fix: remove deprecated legacy code
- feat: add input validation for user registration form
- ci: resolve failing CI pipeline tests
- feat: implement analytics tracking for user engagement
- fix: strengthen authentication password requirements
- feat: improve form accessibility for screen readers
- infra: update deployment scripts for new server setup
- infra: add Redis caching to AWS CDK
- dev: enhance developer experience with improved logging
- dev: add Claude command for better testing
- build: update dependencies to latest versions

Example of splitting commits:

- First commit: feat: add new solc version type definitions
- Second commit: docs: update documentation for new solc versions
- Third commit: chore: update package.json dependencies
- Fourth commit: feat: add type definitions for new API endpoints
- Fifth commit: feat: improve concurrency handling in worker threads
- Sixth commit: fix: resolve linting issues in new code
- Seventh commit: test: add unit tests for new solc version features
- Eighth commit: fix: update dependencies with security vulnerabilities

## Command Options

- --no-verify: Skip running the pre-commit checks (lint, build, generate:docs)

## Important Notes

- By default, pre-commit checks will run to ensure code quality
- If these checks fail, you'll be asked if you want to proceed with the commit anyway or fix the issues first
- If specific files are already staged, the command will only commit those files
- If no files are staged, it will automatically stage all modified and new files
- The commit message will be constructed based on the changes detected
- Before committing, the command will review the diff to identify if multiple commits would be more appropriate
- If suggesting multiple commits, it will help you stage and commit the changes separately
- Always reviews the commit diff to ensure the message matches the changes
