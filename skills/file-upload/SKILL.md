---
name: file-upload
description: Upload a file and return a shareable public link when the user asks to share a PDF, ZIP, document, image, video, or other file, or to update or delete a file at a link that was already shared. Works for email links, messages, PRs, and comments.
---

# File upload

This service creates public URLs. Every response requests no indexing, but anyone with a URL can read the file.
A private GitHub repository does not make an externally hosted file private. Do not use this service for content
that must require authentication. Cloudflare Access is a separate capability.

Share a file only on existing authorization: the user's request, or a skill that tells you to publish, such as
`html-communication` or the Proof section of `file-pr`. Creating a document does not by itself authorize publishing it.
Upload the selected file unchanged and return its link so the user can share it wherever they need.

## Run the script

Run `scripts/file-host` from this skill's directory, by its absolute path. It prints the file's URL on stdout and the
HTTP status on stderr, and exits non-zero on an HTTP error.

```bash
file-host put /absolute/path/to/recording.mp4
file-host replace /absolute/path/to/report.html https://files.example.com/uuid/report.html
file-host delete https://files.example.com/uuid/report.html
```

The script reads `FILE_HOST_URL` and `FILE_HOST_TOKEN` from the environment. The shell exports both on machines set
up with chezmoi, so uploads need no 1Password unlock and work while nobody is at the keyboard. When either is unset,
the script reads it from 1Password with `op read`, which can wait on a desktop unlock prompt. If a value is still
missing after the lookup, report which one. Do not guess a hostname, print the token, or commit these values.

## Upload a file

`put` uploads one regular file, up to 100,000,000 bytes. The service sanitizes the file's name and adds a random
directory, so repeated names create separate files. A successful upload returns HTTP 201 with the public URL. Use
that returned URL directly.

On HTTP 401, stop and report an invalid token. On HTTP 413, report the size limit. Do not automatically retry
an upload after a connection failure: the first upload might already have succeeded.

Verify the returned URL with `curl --silent --show-error --fail --head "$url"`. Check the HTTP status and
`Content-Type` before embedding it.

## Replace a file

`replace` puts the new version at the file's existing URL. The URL and any `?preview=1` link stay the same, so
nobody needs a new link. The local filename does not need to match. The previous content is gone; the service keeps
no history.

A successful replacement returns HTTP 200 with the same URL, and it is safe to retry. HTTP 404 means nothing
exists at that URL, so check the link. Do not fall back to `put`: that creates a separate file with a new link.

## Delete a file

Delete only when the user asks for it and names the link. There is no undo and no listing to find it again.

HTTP 204 means the file is gone and the link now returns 404. HTTP 404 means nothing exists at that URL.

## Share the result

- Embed PNG, JPEG, GIF, and WebP images as `![description](URL)`.
- Link videos as `[Watch recording](URL)`. GitHub does not play externally hosted videos inline, so add a GIF
  preview where one helps.
- Link other files as `[Download filename](URL)`.
- For a self-contained HTML preview, append `?preview=1` to the returned `.html` or `.htm` URL and share
  `[View report](URL?preview=1)`. Verify that URL with HEAD: expect `text/html; charset=utf-8` and an inline
  `Content-Disposition`. The original URL still downloads the file.
- HTML previews run as ordinary webpages without a sandbox. Links, scripts, exports, printing, and forms
  follow normal browser rules. Include print CSS in reports intended for printing; forms need a receiving service.
- SVG and other attachment formats still download. The preview option applies only to HTML.

`ffmpeg` is installed. For a clip shorter than about 30 seconds, make a GIF preview, upload it separately, and
embed it above the full video link:

```bash
ffmpeg -i recording.mp4 -vf "fps=10,scale=800:-1" -loop 0 preview.gif
```

Links last while the file and hosting remain available.
