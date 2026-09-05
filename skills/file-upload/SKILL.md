---
name: file-upload
description: Upload a file and return a shareable public link when the user asks to share a PDF, ZIP, document, image, video, or other file. Works for email links, messages, PRs, and comments.
---

# File upload

This service creates public URLs. Every response requests no indexing, but anyone with a URL can read the file.
A private GitHub repository does not make an externally hosted file private. Do not use this service for content
that must require authentication. Cloudflare Access and HTML site publishing are separate capabilities.

Use existing authorization to share the file. Creating a document does not by itself authorize publishing it.
Upload the selected file unchanged and return its link so the user can share it wherever they need.

## Upload a file

Read `FILE_HOST_URL` and `FILE_HOST_TOKEN` from the environment. When either is unset, read it from 1Password
with `op read`. The URL is the HTTPS origin of the upload service, without a file path. If a value is still
missing after the lookup, report which one. Do not guess a hostname, print the token, or commit these values.

| Variable | 1Password reference |
| --- | --- |
| `FILE_HOST_URL` | `op://AGLara/Agent Files Service - Cloudflare/URL` |
| `FILE_HOST_TOKEN` | `op://AGLara/Agent Files Service - Cloudflare/password` |

Upload one regular file, up to 100,000,000 bytes. Use this command with the selected local path:

```bash
file='/absolute/path/to/recording.mp4'
: "${FILE_HOST_URL:=$(op read 'op://AGLara/Agent Files Service - Cloudflare/URL')}"
: "${FILE_HOST_TOKEN:=$(op read 'op://AGLara/Agent Files Service - Cloudflare/password')}"
: "${FILE_HOST_URL:?FILE_HOST_URL is not set and the 1Password lookup failed}"
: "${FILE_HOST_TOKEN:?FILE_HOST_TOKEN is not set and the 1Password lookup failed}"
printf 'X-Upload-Token: %s\n' "$FILE_HOST_TOKEN" |
	curl --silent --show-error --fail-with-body --globoff --proto '=https' \
		--header @- --upload-file "$file" "${FILE_HOST_URL%/}/"
```

The trailing slash lets curl append and encode the file's basename. The service sanitizes that name and adds
a random directory, so repeated names create separate files. A successful upload returns HTTP 201 with the
public URL as plain text. Use that returned URL directly.

On HTTP 401, stop and report an invalid token. On HTTP 413, report the size limit. Do not automatically retry
an upload after a connection failure: the first upload might already have succeeded.

Verify the returned URL with `curl --silent --show-error --fail --head "$url"`. Check the HTTP status and
`Content-Type` before embedding it.

## Share the result

- Embed PNG, JPEG, GIF, and WebP images as `![description](URL)`.
- Link videos as `[Watch recording](URL)`. GitHub does not play externally hosted videos inline, so add a GIF
  preview where one helps.
- Link other files as `[Download filename](URL)`.
- HTML, SVG, and other active formats download as attachments. They are not published as executable sites.

`ffmpeg` is installed. For a clip shorter than about 30 seconds, make a GIF preview, upload it separately, and
embed it above the full video link:

```bash
ffmpeg -i recording.mp4 -vf "fps=10,scale=800:-1" -loop 0 preview.gif
```

Links last while the file and hosting remain available.
