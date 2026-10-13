---
name: domain-finder
description: Find available domain names for the current project. Reads the codebase for its purpose, generates candidates, and checks each with RDAP, confirmed by whois and dig. Use when asked for domain ideas or whether domains are available.
allowed-tools: Read, Glob, Grep, Bash(curl:*), Bash(whois:*), Bash(dig:*), Write
---

# Domain finder

## 1. Understand the project

Read `README.md`, the rules file, and the main source entry points for the product's purpose, its audience, and the
words it uses for itself. If the user gave a hint, it is the primary basis for every candidate.

## 2. Generate candidates

Check at least 20 to 30. Mix name variations, descriptive and action names, compounds, and a few prefixed (`get-`,
`try-`) or suffixed (`-app`, `-hq`) forms. Prefer short (under 15 characters), no hyphens, memorable, and clearly
about the product; check a hyphenated form only as a fallback.

TLDs, in order: `.com`, then `.com.au` and `.au` for an Australian-market product, then `.io`, `.app`, `.dev`, `.co`,
and a topical TLD when one fits (`.email`, `.tools`).

## 3. Check availability

RDAP first. It gives one machine-readable answer across most TLDs, unlike whois output, which varies by registry.

```bash
curl -sL -o /dev/null -w "%{http_code}" https://rdap.org/domain/<domain>
```

- `200`: taken. Definitive.
- `404`: promising, not proof. Some TLDs (`.io`, `.co`) are missing from the RDAP bootstrap registry and return 404
  for registered domains too. Confirm with whois and dig.
- Anything else: inconclusive. Fall back to whois and dig.

```bash
# Indicators sit at the start of a line; a loose match on "available" hits
# registry Terms of Use boilerplate and reports registered domains as free.
whois <domain> 2>/dev/null | grep -iE "^(no match|not found|domain not found|no data found|no entries found|status:\s*free)"
dig +short NS <domain>
```

Available only when RDAP returned 404, whois shows an indicator, and dig returns no NS records. Taken when any of the
three says so. Pause briefly between whois queries; registries rate-limit.

## 4. Write the result

Write `out/available-domains.md`: a one-line project summary, a table of available domains (domain, TLD, note), a
table of checked-but-taken domains with their registrar or status, and the top three recommendations with a sentence
of reasoning each. Record the timestamp and the hint, if any.
