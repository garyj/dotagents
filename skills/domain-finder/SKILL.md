---
name: domain-finder
description: >-
  Discovers and checks availability of domain names suitable for this project.
  Analyzes the codebase to understand the project purpose, generates relevant
  domain name suggestions, and uses whois/dig to verify availability.
  Use when you need to find available domains for the project.
allowed-tools: Read, Glob, Grep, Bash(whois:*), Bash(dig:*), Write
---

# Domain Finder Agent

Discovers available domain names relevant to this project by analyzing the codebase and checking domain availability.

## Workflow

### Phase 1: Understand the Project

1. Read key files to understand what this project does:
   - `README.md` for project overview
   - `CLAUDE.md` for technical context
   - Key source files in `src/` to understand functionality
   - Look for project name patterns, keywords, and purpose

2. Identify core concepts:
   - Primary function (email domain checking, deliverability, DNS analysis)
   - Target audience (developers, businesses, IT admins)
   - Key terms (email, domain, check, verify, deliverability, DNS, SPF, DKIM, DMARC)

### Phase 2: Generate Domain Candidates

Generate domain name candidates using these strategies:

**Naming patterns:**

- Project name variations: `emdomcheck`, `domcheck`, `emaildomaincheck`
- Descriptive names: `emailverify`, `domainhealth`, `mailcheck`
- Action-oriented: `checkmail`, `verifydomain`, `testmail`
- Compound words: `emailchecker`, `domainscanner`, `mailvalidator`
- With prefixes: `my-`, `get-`, `try-`, `go-`
- With suffixes: `-app`, `-io`, `-hq`, `-lab`

**Relevant TLDs (prioritize):**

- `.com` - Most recognized
- `.io` - Tech/developer focus
- `.app` - Web applications
- `.dev` - Developer tools
- `.email` - Email-specific
- `.tools` - Utility focus
- `.co` - Startup friendly
- `.net` - Network/technical

**If a hint is provided:**
Use the hint as the primary basis for domain generation, creating variations around it.

### Phase 3: Check Domain Availability

For each candidate domain, check availability using:

```bash
# Primary check - whois
whois <domain> 2>/dev/null | grep -iE "(no match|not found|available|no data found|domain not found)"

# Secondary check - dig for NS records
dig +short NS <domain>
```

**Interpretation:**

- Available: whois shows "No match" / "Not found" / "Available" AND dig returns no NS records
- Taken: whois shows registrar info OR dig returns NS records

### Phase 4: Output Results

Write results to `out/available-domains.md` with:

```markdown
# Available Domains for [Project Name]

Generated: [timestamp]
Hint provided: [hint or "none"]

## Project Summary
[Brief description of what the project does]

## Available Domains

| Domain | TLD | Notes |
|--------|-----|-------|
| example.io | .io | Short, memorable |
| ... | ... | ... |

## Checked but Taken

| Domain | Registrar/Status |
|--------|-----------------|
| example.com | Registered (GoDaddy) |
| ... | ... |

## Recommendations

Top 3 recommendations with reasoning:
1. **domain.io** - Best choice because...
2. **domain.app** - Good alternative...
3. **domain.dev** - Developer-focused...
```

## Usage

The agent accepts an optional hint parameter:

- No hint: Generates names based purely on project analysis
- With hint: Uses the hint as the primary basis (e.g., hint="mailguard" generates mailguard.com, mailguard.io, etc.)

## Important Notes

- Check at least 20-30 domain candidates
- Rate limit whois queries (brief pause between checks) to avoid being blocked
- Prefer shorter domains (under 15 characters)
- Avoid hyphens when possible (but check hyphenated versions too)
- Consider memorable, brandable names
- Focus on domains that clearly convey the purpose
