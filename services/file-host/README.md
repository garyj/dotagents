# File host

The file host stores agent uploads in a private R2 bucket and serves public URLs through a Worker.
The upload hostname is configured in Cloudflare's Custom Domain settings and in the file-upload skill's defaults.
The Worker returns links using the origin of the upload request.

[Set up the service](SETUP.md). Agents use the [file-upload skill](../../skills/file-upload/SKILL.md).

## HTTP interface

| Request | Result |
| --- | --- |
| `PUT /filename` with `X-Upload-Token` | Stores a new object and returns its URL with HTTP 201 |
| `GET /uuid/filename` | Returns the public file |
| `HEAD /uuid/filename` | Returns metadata without the file body |
| `GET` with a single byte `Range` | Returns HTTP 206, or HTTP 416 for an invalid range |
| `GET` or `HEAD` with a matching `If-None-Match` | Returns HTTP 304 |
| Other methods | Returns HTTP 405 |

Uploads require a valid `FILE_HOST_TOKEN` and a `Content-Length` no greater than 100,000,000 bytes.
HTTP 401 means the token is missing or incorrect. HTTP 411 means the length is missing. HTTP 413 means the file
is too large. A missing server token disables uploads with HTTP 503. Storage failures return HTTP 500.

Each upload gets a new UUID directory. The service exposes no listing, overwrite, or deletion API.
Empty files are supported. Multipart uploads are not implemented.

## File display and privacy

PNG, JPEG, GIF, WebP, AVIF, MP4, WebM, MOV, MP3, WAV, and OGG have inline media types based on their extensions.
Browser playback depends on the codec. Other formats, including HTML, SVG, PDF, and ZIP, use
`application/octet-stream` and download as attachments. Client-supplied content types are not trusted.

All responses include `X-Robots-Tag: noindex, nofollow`, `X-Content-Type-Options: nosniff`, and
`Referrer-Policy: no-referrer`. These headers do not authenticate readers or prevent someone from sharing a URL.
The service does not block crawling through `robots.txt`, because crawlers must fetch a URL to see `noindex`.

File responses allow caching for one hour. Copies may remain in browser or GitHub caches after removal from R2.
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
