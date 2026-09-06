# File host

The file host stores agent uploads in a private R2 bucket and serves public URLs through a Worker.
The upload hostname is configured in Cloudflare's Custom Domain settings and in the file-upload skill's defaults.
The Worker returns links using the origin of the upload request.

[Set up the service](SETUP.md). Agents use the [file-upload skill](../../skills/file-upload/SKILL.md).

## HTTP interface

| Request | Result |
| --- | --- |
| `PUT /filename` with `X-Upload-Token` | Stores a new object and returns its URL with HTTP 201 |
| `PUT /uuid/filename` with `X-Upload-Token` | Replaces the object at that URL and returns the URL with HTTP 200 |
| `DELETE /uuid/filename` with `X-Upload-Token` | Removes the object and returns HTTP 204 |
| `GET /uuid/filename` | Returns the public file |
| `GET /uuid/report.html?preview=1` | Displays HTML in the browser |
| `HEAD /uuid/filename` | Returns metadata without the file body |
| `GET` with a single byte `Range` | Returns HTTP 206, or HTTP 416 for an invalid range |
| `GET` or `HEAD` with a matching `If-None-Match` | Returns HTTP 304 |
| Other methods | Returns HTTP 405 |

Uploads and deletions require a valid `FILE_HOST_TOKEN`. Uploads also need a `Content-Length` no greater than
100,000,000 bytes. HTTP 401 means the token is missing or incorrect. HTTP 411 means the length is missing.
HTTP 413 means the file is too large. HTTP 404 on a replacement or deletion means nothing exists at that path.
A missing server token disables uploads and deletions with HTTP 503. Storage failures return HTTP 500.

Each upload to the root gets a new UUID directory. Uploading to an existing object's path replaces it and keeps
the URL, so shared links and `?preview=1` links stay valid. Deleting an object makes its URL return 404. Neither
can be undone: the service keeps no versions and exposes no listing API. Empty files are supported. Multipart
uploads are not implemented.

## File display and privacy

PNG, JPEG, GIF, WebP, AVIF, MP4, WebM, MOV, MP3, WAV, and OGG have inline media types based on their extensions.
Browser playback depends on the codec. Other formats, including HTML, SVG, PDF, and ZIP, use
`application/octet-stream` and download as attachments. Client-supplied content types are not trusted.

Append `?preview=1` to a `.html` or `.htm` URL to display it as `text/html; charset=utf-8` with an inline
disposition. Extension matching is case-insensitive. Removing the query restores the download. This works
for existing uploads and for GET, HEAD, conditional, and range requests. Other formats ignore the option.
HTML previews have no sandbox or added Content Security Policy, so links, scripts, exports, print buttons,
and forms follow normal browser rules. Use self-contained HTML; the service does not bundle local assets.

All responses include `X-Robots-Tag: noindex, nofollow`, `X-Content-Type-Options: nosniff`, and
`Referrer-Policy: no-referrer`. These headers do not authenticate readers or prevent someone from sharing a URL.
The service does not block crawling through `robots.txt`, because crawlers must fetch a URL to see `noindex`.

File responses use `Cache-Control: no-cache`, so browsers revalidate with the ETag on every visit and pick up a
replacement straight away. Other caches, such as GitHub's image proxy, may hold a copy for a while.
Files have no automatic expiry. Direct bucket publication, Worker preview URLs, and `workers.dev` access are
not part of this setup. Workers Logs records the method, URL, and status of every request, so the Cloudflare
dashboard shows which files are fetched and how often. Application error logs omit URLs and tokens.

## Project commands

Commands run from `services/file-host/` with Node 24 and the pnpm version pinned in `package.json`.

| Command | Purpose |
| --- | --- |
| `pnpm dev` | Runs the Worker with local R2 storage |
| `pnpm types` | Generates binding and runtime types from Wrangler |
| `pnpm typecheck` | Generates types and checks TypeScript |
| `pnpm lint` | Checks JavaScript and TypeScript, including floating promises |
| `pnpm test` | Builds locally and exercises HTTP behavior with Miniflare's R2 implementation |
| `pnpm check` | Runs type-checking, linting, and tests |
| `pnpm build` | Bundles the Worker with a deployment dry run |
| `pnpm deploy` | Deploys the Worker to the selected Cloudflare account |

The service has its own package manifest and lockfile. Generated types, local secrets, R2 data, and build output
are ignored by Git. Uploads do not require Git commits or Worker redeployments.
