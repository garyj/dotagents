---
name: context7-mcp
description: Fetch current library and framework documentation through the Context7 MCP server before answering setup, API, or code-example questions about a named library, framework, or SDK.
---

# Context7

Use the Context7 MCP tools, when the session has them, instead of training data for any question about a named
library, framework, or SDK, including setup and configuration.

1. Call `resolve-library-id` with the library name and the user's full question as `query`. Pick the exact name
   match, prefer the official package over forks, and take the version-specific id when the user named a version.
2. Call `query-docs` with that id and the user's specific question.
3. Answer from the fetched docs, with their code examples, and cite the library version when it matters.
