import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
import { after, before, test } from "node:test";
import { convertV4MiniflareOptions, Miniflare } from "miniflare";

const config = JSON.parse(await readFile(new URL("../wrangler.jsonc", import.meta.url), "utf8"));
const token = randomUUID();
let runtime;

before(async () => {
  runtime = new Miniflare(convertV4MiniflareOptions({
    modules: true,
    scriptPath: "dist/index.js",
    compatibilityDate: config.compatibility_date,
    compatibilityFlags: config.compatibility_flags,
    bindings: { FILE_HOST_TOKEN: token },
    r2Buckets: { FILES: "test-files" },
    cf: false,
  }));
  await runtime.ready;
});

after(async () => { await runtime?.dispose(); });

async function put(url, body, headers = {}) {
  return runtime.dispatchFetch(url, {
    method: "PUT",
    headers: { "X-Upload-Token": token, "Content-Length": String(Buffer.byteLength(body)), ...headers },
    body,
  });
}

async function upload(name, body = "file contents", headers = {}) {
  return put(`https://files.example.com/${encodeURIComponent(name)}`, body, headers);
}

async function publishedUrl(response) {
  assert.equal(response.status, 201, await response.clone().text());
  const url = (await response.text()).trim();
  assert.equal(response.headers.get("Location"), url);
  assert.match(url, /^https:\/\/files\.example\.com\/[0-9a-f-]{36}\//);
  assert.equal(response.headers.get("X-Robots-Tag"), "noindex, nofollow");
  return url;
}

test("requires a valid token before accepting an upload", async () => {
  for (const headers of [{}, { "X-Upload-Token": "incorrect" }]) {
    const response = await runtime.dispatchFetch("https://files.example.com/image.png", {
      method: "PUT", headers, body: "private bytes",
    });
    assert.equal(response.status, 401);
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    assert.equal(response.headers.get("X-Robots-Tag"), "noindex, nofollow");
  }
  const bucket = await runtime.getR2Bucket("FILES");
  assert.equal((await bucket.list()).objects.length, 0);
});

test("fails closed if the upload secret is missing", async () => {
  const unconfigured = new Miniflare(convertV4MiniflareOptions({
    modules: true,
    scriptPath: "dist/index.js",
    compatibilityDate: config.compatibility_date,
    compatibilityFlags: config.compatibility_flags,
    r2Buckets: ["FILES"],
    cf: false,
  }));
  try {
    const response = await unconfigured.dispatchFetch("https://files.example.com/a.png", {
      method: "PUT", body: "bytes",
    });
    assert.equal(response.status, 503);
  } finally {
    await unconfigured.dispose();
  }
});

test("publishes binary images with noindex and safe display headers", async () => {
  const bytes = Buffer.from("89504e470d0a1a0a000102ff", "hex");
  const url = await publishedUrl(await upload("screen shot.PNG", bytes));
  assert.ok(url.endsWith("/screen-shot.PNG"));
  const response = await runtime.dispatchFetch(url);
  assert.equal(response.status, 200);
  assert.deepEqual(Buffer.from(await response.arrayBuffer()), bytes);
  assert.equal(response.headers.get("Content-Type"), "image/png");
  assert.equal(response.headers.get("Content-Disposition"), 'inline; filename="screen-shot.PNG"');
  assert.equal(response.headers.get("X-Robots-Tag"), "noindex, nofollow");
  assert.equal(response.headers.get("X-Content-Type-Options"), "nosniff");
  assert.equal(response.headers.get("Referrer-Policy"), "no-referrer");
});

test("preserves earlier files when the same name is uploaded again", async () => {
  const first = await publishedUrl(await upload("same.gif", "first"));
  const second = await publishedUrl(await upload("same.gif", "second"));
  assert.notEqual(first, second);
  assert.equal(await (await runtime.dispatchFetch(first)).text(), "first");
  assert.equal(await (await runtime.dispatchFetch(second)).text(), "second");
});

test("returns the upload origin without a configured hostname", async () => {
  const response = await runtime.dispatchFetch("https://uploads.example.net/image.png", {
    method: "PUT", headers: { "X-Upload-Token": token, "Content-Length": "5" }, body: "bytes",
  });
  assert.equal(response.status, 201);
  assert.ok((await response.text()).startsWith("https://uploads.example.net/"));
});

test("serves filenames that start with an underscore", async () => {
  for (const name of ["_photo.png", "_notice.pdf", "__init__.py", "_"]) {
    const url = await publishedUrl(await upload(name, "unchanged bytes"));
    assert.ok(url.endsWith(`/${name}`));
    assert.equal((await runtime.dispatchFetch(url, { method: "HEAD" })).status, 200);
    const response = await runtime.dispatchFetch(url);
    assert.equal(response.status, 200);
    assert.equal(await response.text(), "unchanged bytes");
  }
});

test("forces HTML, SVG, unknown formats, and prototype property names to download", async () => {
  for (const name of ["report.html", "diagram.svg", "data.zip", "report.pdf", "test.constructor", "test.__proto__"]) {
    const url = await publishedUrl(await upload(name, "<script>alert(1)</script>", {
      "Content-Type": "text/html",
    }));
    const response = await runtime.dispatchFetch(url);
    assert.equal(response.headers.get("Content-Type"), "application/octet-stream");
    assert.ok(response.headers.get("Content-Disposition").startsWith("attachment;"));
    await response.arrayBuffer();
  }
});

test("previews existing HTML uploads and preserves the download URL", async () => {
  const html = '<!doctype html><meta charset="utf-8"><h1>Owner report</h1><script>document.title = "Report"</script>';
  for (const name of ["report.html", "report.HTM"]) {
    const url = await publishedUrl(await upload(name, html));
    const preview = `${url}?preview=1`;
    for (const method of ["GET", "HEAD"]) {
      const response = await runtime.dispatchFetch(preview, { method });
      assert.equal(response.status, 200);
      assert.equal(response.headers.get("Content-Type"), "text/html; charset=utf-8");
      assert.equal(response.headers.get("Content-Disposition"), `inline; filename="${name}"`);
      assert.equal(response.headers.get("Content-Security-Policy"), null);
      assert.equal(response.headers.get("X-Robots-Tag"), "noindex, nofollow");
      if (method === "HEAD") assert.equal(response.headers.get("Content-Length"), String(Buffer.byteLength(html)));
      assert.equal(await response.text(), method === "HEAD" ? "" : html);
    }
    const head = await runtime.dispatchFetch(preview, { method: "HEAD" });
    const cached = await runtime.dispatchFetch(preview, { headers: { "If-None-Match": head.headers.get("ETag") } });
    assert.equal(cached.status, 304);
    assert.equal(cached.headers.get("Content-Type"), "text/html; charset=utf-8");
    const range = await runtime.dispatchFetch(preview, { headers: { Range: "bytes=0-14" } });
    assert.equal(range.status, 206);
    assert.equal(range.headers.get("Content-Type"), "text/html; charset=utf-8");
    assert.equal(await range.text(), html.slice(0, 15));
    for (const query of ["", "?preview=0", "?preview=true"]) {
      const download = await runtime.dispatchFetch(`${url}${query}`);
      assert.equal(download.headers.get("Content-Type"), "application/octet-stream");
      assert.equal(download.headers.get("Content-Disposition"), `attachment; filename="${name}"`);
      assert.equal(await download.text(), html);
    }
  }
});

test("preview does not change other file formats", async () => {
  for (const [name, contentType] of [["image.png", "image/png"], ["diagram.svg", "application/octet-stream"], ["report.pdf", "application/octet-stream"]]) {
    const url = await publishedUrl(await upload(name));
    const response = await runtime.dispatchFetch(`${url}?preview=1`);
    assert.equal(response.headers.get("Content-Type"), contentType);
    assert.equal(await response.text(), "file contents");
  }
});

test("rejects path names and malformed URL encoding", async () => {
  for (const name of ["folder/file.png", "folder\\file.png", "a".repeat(256), "\uFB03".repeat(255), "..."]) {
    assert.equal((await upload(name)).status, 400);
  }
  const response = await runtime.dispatchFetch("https://files.example.com/%ZZ", {
    method: "PUT", headers: { "X-Upload-Token": token }, body: "bytes",
  });
  assert.equal(response.status, 400);
});

test("serves video byte ranges, including suffix and open-ended requests", async () => {
  const url = await publishedUrl(await upload("recording.mp4", "0123456789"));
  for (const [range, expected, contentRange] of [
    ["bytes=2-5", "2345", "bytes 2-5/10"],
    ["bytes=7-", "789", "bytes 7-9/10"],
    ["bytes=-3", "789", "bytes 7-9/10"],
    ["bytes=8-999", "89", "bytes 8-9/10"],
  ]) {
    const response = await runtime.dispatchFetch(url, { headers: { Range: range } });
    assert.equal(response.status, 206);
    assert.equal(response.headers.get("Content-Range"), contentRange);
    assert.equal(response.headers.get("Content-Length"), String(expected.length));
    assert.equal(response.headers.get("Content-Type"), "video/mp4");
    assert.equal(await response.text(), expected);
  }
});

test("returns 416 for unsatisfiable ranges", async () => {
  const url = await publishedUrl(await upload("range.webm", "0123456789"));
  for (const range of ["bytes=20-", "bytes=5-2", "bytes=-0", "bytes=", "bytes=0-1,5-6"]) {
    const response = await runtime.dispatchFetch(url, { headers: { Range: range } });
    assert.equal(response.status, 416);
    assert.equal(response.headers.get("Content-Range"), "bytes */10");
    assert.equal(response.headers.get("X-Robots-Tag"), "noindex, nofollow");
  }
});

test("supports HEAD and conditional downloads", async () => {
  const url = await publishedUrl(await upload("head.png", "0123456789"));
  const head = await runtime.dispatchFetch(url, { method: "HEAD", headers: { Range: "bytes=0-1" } });
  assert.equal(head.status, 200);
  assert.equal(head.headers.get("Content-Length"), "10");
  assert.equal(head.headers.get("Accept-Ranges"), "bytes");
  assert.equal(await head.text(), "");
  const etag = head.headers.get("ETag");
  for (const value of [etag, `W/${etag}`, `"other", ${etag}`, "*"]) {
    const cached = await runtime.dispatchFetch(url, { headers: { "If-None-Match": value } });
    assert.equal(cached.status, 304);
    assert.equal(await cached.text(), "");
  }
  const changed = await runtime.dispatchFetch(url, {
    headers: { Range: "bytes=0-1", "If-Range": '"old-etag"' },
  });
  assert.equal(changed.status, 200);
  assert.equal(await changed.text(), "0123456789");
});

test("has no public listing endpoint and rejects other methods", async () => {
  const url = await publishedUrl(await upload("retained.png"));
  for (const path of ["/", "/robots.txt", "/unknown", "/00000000-0000-0000-0000-000000000000/missing.png"]) {
    assert.equal((await runtime.dispatchFetch(`https://files.example.com${path}`)).status, 404);
  }
  const post = await runtime.dispatchFetch(url, { method: "POST", headers: { "X-Upload-Token": token }, body: "x" });
  assert.equal(post.status, 405);
  assert.equal(post.headers.get("Allow"), "DELETE, GET, HEAD, PUT");
  assert.equal(await (await runtime.dispatchFetch(url)).text(), "file contents");
});

test("deletes a file with the token and then serves 404", async () => {
  const url = await publishedUrl(await upload("gone.png"));
  assert.equal((await runtime.dispatchFetch(url, { method: "DELETE" })).status, 401);
  assert.equal(await (await runtime.dispatchFetch(url)).text(), "file contents");
  const removed = await runtime.dispatchFetch(url, { method: "DELETE", headers: { "X-Upload-Token": token } });
  assert.equal(removed.status, 204);
  assert.equal(await removed.text(), "");
  assert.equal((await runtime.dispatchFetch(url)).status, 404);
  const again = await runtime.dispatchFetch(url, { method: "DELETE", headers: { "X-Upload-Token": token } });
  assert.equal(again.status, 404);
});

test("replaces a file in place when its URL is uploaded to again", async () => {
  const url = await publishedUrl(await upload("report.html", "<h1>Draft</h1>"));
  const original = (await runtime.dispatchFetch(url, { method: "HEAD" })).headers.get("ETag");
  const replaced = await put(url, "<h1>Final</h1>");
  assert.equal(replaced.status, 200, await replaced.clone().text());
  assert.equal((await replaced.text()).trim(), url);
  const preview = await runtime.dispatchFetch(`${url}?preview=1`);
  assert.equal(await preview.text(), "<h1>Final</h1>");
  assert.equal(preview.headers.get("Content-Type"), "text/html; charset=utf-8");
  assert.equal(preview.headers.get("Cache-Control"), "no-cache");
  assert.notEqual(preview.headers.get("ETag"), original);
  assert.equal((await runtime.dispatchFetch(url, { headers: { "If-None-Match": original } })).status, 200);
});

test("refuses to replace a missing file or one under another name", async () => {
  const url = await publishedUrl(await upload("keep.png", "original"));
  const directory = url.slice(0, url.lastIndexOf("/"));
  for (const target of [`${directory}/other.png`, `https://files.example.com/${randomUUID()}/keep.png`]) {
    assert.equal((await put(target, "replacement")).status, 404);
    assert.equal((await runtime.dispatchFetch(target)).status, 404);
  }
  assert.equal((await put(url, "replacement", { "X-Upload-Token": "incorrect" })).status, 401);
  assert.equal(await (await runtime.dispatchFetch(url)).text(), "original");
});

test("accepts an empty file", async () => {
  const url = await publishedUrl(await upload("empty.txt", ""));
  const response = await runtime.dispatchFetch(url);
  assert.equal(response.status, 200);
  assert.equal((await response.arrayBuffer()).byteLength, 0);
});

test("requires a known upload size", async () => {
  const stream = new ReadableStream({
    start(controller) { controller.enqueue(new TextEncoder().encode("bytes")); controller.close(); },
  });
  const response = await runtime.dispatchFetch("https://files.example.com/stream.mp4", {
    method: "PUT", headers: { "X-Upload-Token": token }, body: stream, duplex: "half",
  });
  assert.equal(response.status, 411);
});

test("streams a 100 MB file and rejects a larger upload", async () => {
  const bytes = Buffer.alloc(100_000_000, 42);
  const url = await publishedUrl(await upload("large.mp4", bytes));
  const head = await runtime.dispatchFetch(url, { method: "HEAD" });
  assert.equal(head.headers.get("Content-Length"), "100000000");
  const tail = await runtime.dispatchFetch(url, { headers: { Range: "bytes=-8" } });
  assert.deepEqual(Buffer.from(await tail.arrayBuffer()), Buffer.alloc(8, 42));
  const oversized = await upload("too-large.mp4", Buffer.alloc(100_000_001));
  assert.equal(oversized.status, 413);
});
