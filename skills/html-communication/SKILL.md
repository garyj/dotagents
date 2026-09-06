---
name: html-communication
description: Present a plan, spec, write-up, findings, comparison, or UI mocks as one self-contained HTML page and publish it. Use when the user asks for an HTML document, or says "HTML" with no other context. Not for HTML that ships in a product.
---

# HTML communication

Write one self-contained HTML file, then publish it where the session can host it.

## Write the page

Write it like a spec, not a landing page: dense and scannable, with no hero section, decorative chrome, or marketing voice. Apply the `unslop` skill to the prose.

- Keep the file under 512 KB with everything inline: CSS, SVG, and images as HTTPS or data URLs.
- Use semantic HTML. Headings, lists, and tables carry the structure.
- Default to a true black background (`#000`), white primary text, and dark gray only for secondary surfaces or accents. Set the background and text color on `body` explicitly.
- Make it readable on a phone: a responsive viewport and no fixed-width layout. A wide table or code block scrolls inside its own container.
- Add an inline classic script only when interactivity materially helps, and keep the page useful without it. A host may block storage, fetch, workers, frames, forms, and popups.
- In a script-free file, give external links `target="_blank"` and `rel="noopener noreferrer"`. If the file has a script, omit `target="_blank"`.

Never include external or module scripts, inline event handlers, `javascript:` URLs, forms, frames, embeds, objects, meta refresh, linked stylesheets, secrets, private URLs, or local filesystem paths.

### UI mocks

When the user asks for variants, render real styled variants rather than descriptions. Label them A, B, C, and so on, and lay them out side by side so the user can compare and pick by letter.

## Keep one file per document

Write the file where the user asked. Otherwise use the session's scratchpad directory. Edit the same file across iterations so its published URL stays stable. Create a second file only when the user asks for a separate draft.

## Publish

Publishing is part of the job. Do not ask for separate permission and do not stop at the local file. Say which kind of publish you are doing, public link or private artifact, before you publish and again beside the URL in the reply.

Publish publicly by default. Write a complete document with `<!DOCTYPE html>` and publish it with the `file-upload` skill. Share the returned URL with `?preview=1` appended. On later iterations, replace the file at that same URL so the link stays valid.

If the user asks for a private artifact, publish with the Artifact tool instead:

- Write the page the way the tool requires: no `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>` tags, with `<title>` and `<style>` first. The tool wraps the page itself. Pass an emoji favicon on the first publish.
- Publish the same file path again to update the URL. To update an artifact from an earlier session, pass its URL.
- If the session has no Artifact tool, report the local path and say that this session cannot publish privately.

Report the local path and the URL in the reply. Never claim the page is hosted before the publish succeeds. Do not open it in a browser unless the user asks.
