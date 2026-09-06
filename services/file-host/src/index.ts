const MAX_UPLOAD_BYTES = 100_000_000;
const KEY_PATTERN = /^\/[0-9a-f-]{36}\/[a-zA-Z0-9_][a-zA-Z0-9._-]*$/;
const INLINE_TYPES: Record<string, string> = {
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  gif: "image/gif",
  webp: "image/webp",
  avif: "image/avif",
  mp4: "video/mp4",
  webm: "video/webm",
  mov: "video/quicktime",
  mp3: "audio/mpeg",
  wav: "audio/wav",
  ogg: "audio/ogg",
};

function reply(body: BodyInit | null, status = 200, headers?: HeadersInit): Response {
  const result = new Response(body, { status, headers });
  result.headers.set("X-Robots-Tag", "noindex, nofollow");
  result.headers.set("X-Content-Type-Options", "nosniff");
  result.headers.set("Referrer-Policy", "no-referrer");
  if (!result.headers.has("Cache-Control")) {
    result.headers.set("Cache-Control", "no-store");
  }
  return result;
}

async function upload(request: Request, env: Env, pathname: string): Promise<Response> {
  if (!env.FILE_HOST_TOKEN) return reply("Upload service is not configured.\n", 503);
  const token = request.headers.get("X-Upload-Token");
  if (!token) return reply("Invalid upload token.\n", 401);
  const encoder = new TextEncoder();
  const [provided, expected] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(token)),
    crypto.subtle.digest("SHA-256", encoder.encode(env.FILE_HOST_TOKEN)),
  ]);
  if (!crypto.subtle.timingSafeEqual(provided, expected)) {
    return reply("Invalid upload token.\n", 401);
  }

  const replacing = KEY_PATTERN.test(pathname);
  let key: string;
  let name: string;
  if (replacing) {
    key = pathname.slice(1);
    name = key.slice(key.indexOf("/") + 1);
    if (!(await env.FILES.head(key))) return reply("Not found.\n", 404);
  } else {
    try {
      name = decodeURIComponent(pathname.slice(1));
    } catch {
      return reply("Invalid filename.\n", 400);
    }
    if (!name || /[/\\]/.test(name)) {
      return reply("Use one filename, without directories.\n", 400);
    }
    name = name.normalize("NFKD").replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^[.-]+/, "");
    if (!name || name.length > 255) return reply("Invalid filename.\n", 400);
    key = `${crypto.randomUUID()}/${name}`;
  }

  const lengthHeader = request.headers.get("Content-Length");
  if (lengthHeader === null) return reply("Content-Length is required.\n", 411);
  if (!/^\d+$/.test(lengthHeader)) return reply("Invalid Content-Length.\n", 400);
  const length = Number(lengthHeader);
  if (!Number.isSafeInteger(length) || length > MAX_UPLOAD_BYTES) {
    return reply("Upload exceeds the 100 MB limit.\n", 413);
  }

  const extension = name.split(".").at(-1)?.toLowerCase() ?? "";
  const inlineType = Object.hasOwn(INLINE_TYPES, extension) ? INLINE_TYPES[extension] : undefined;
  await env.FILES.put(key, request.body ?? new Uint8Array(), {
    httpMetadata: {
      contentType: inlineType ?? "application/octet-stream",
      contentDisposition: `${inlineType ? "inline" : "attachment"}; filename="${name}"`,
    },
  });
  const publicUrl = `${new URL(request.url).origin}/${key}`;
  return reply(`${publicUrl}\n`, replacing ? 200 : 201, {
    "Content-Type": "text/plain; charset=utf-8",
    Location: publicUrl,
  });
}

function byteRange(value: string, size: number): { offset: number; length: number } | null {
  const match = /^bytes=(\d*)-(\d*)$/.exec(value);
  if (!match || (!match[1] && !match[2]) || size === 0) return null;
  if (!match[1]) {
    const suffix = Number(match[2]);
    if (!Number.isSafeInteger(suffix) || suffix <= 0) return null;
    const length = Math.min(suffix, size);
    return { offset: size - length, length };
  }
  const offset = Number(match[1]);
  const end = match[2] ? Number(match[2]) : size - 1;
  if (!Number.isSafeInteger(offset) || !Number.isSafeInteger(end) || offset >= size || end < offset) {
    return null;
  }
  return { offset, length: Math.min(end, size - 1) - offset + 1 };
}

async function download(request: Request, env: Env, pathname: string): Promise<Response> {
  if (!KEY_PATTERN.test(pathname)) return reply("Not found.\n", 404);
  const key = pathname.slice(1);
  const metadata = await env.FILES.head(key);
  if (!metadata) return reply("Not found.\n", 404);

  const headers = new Headers();
  metadata.writeHttpMetadata(headers);
  if (new URL(request.url).searchParams.get("preview") === "1" && /\.html?$/i.test(key)) {
    headers.set("Content-Type", "text/html; charset=utf-8");
    headers.set("Content-Disposition", `inline; filename="${key.split("/")[1]}"`);
  }
  headers.set("ETag", metadata.httpEtag);
  headers.set("Last-Modified", metadata.uploaded.toUTCString());
  headers.set("Accept-Ranges", "bytes");
  headers.set("Cache-Control", "no-cache");

  const ifNoneMatch = request.headers.get("If-None-Match");
  if (ifNoneMatch?.split(",").some((etag) => {
    const value = etag.trim().replace(/^W\//, "");
    return value === "*" || value === metadata.httpEtag;
  })) {
    return reply(null, 304, headers);
  }
  headers.set("Content-Length", String(metadata.size));
  if (request.method === "HEAD") return reply(null, 200, headers);

  const requestedRange = request.headers.get("Range");
  const ifRange = request.headers.get("If-Range");
  const rangeMatches = !ifRange || ifRange === metadata.httpEtag || ifRange === metadata.uploaded.toUTCString();
  const range = requestedRange && rangeMatches ? byteRange(requestedRange, metadata.size) : undefined;
  if (range === null) {
    return reply(null, 416, { "Content-Range": `bytes */${metadata.size}` });
  }

  const object = await env.FILES.get(key, range ? { range } : undefined);
  if (!object) return reply("Not found.\n", 404);
  if (range) {
    headers.set("Content-Length", String(range.length));
    headers.set("Content-Range", `bytes ${range.offset}-${range.offset + range.length - 1}/${metadata.size}`);
  }
  return reply(object.body, range ? 206 : 200, headers);
}

export default {
  async fetch(request, env): Promise<Response> {
    try {
      const { pathname } = new URL(request.url);
      switch (request.method) {
        case "PUT":
          return await upload(request, env, pathname);
        case "GET":
        case "HEAD":
          return await download(request, env, pathname);
        default:
          return reply("Method not allowed.\n", 405, { Allow: "GET, HEAD, PUT" });
      }
    } catch {
      console.error(JSON.stringify({ event: "file_host_request_failed", method: request.method }));
      return reply("File service error.\n", 500);
    }
  },
} satisfies ExportedHandler<Env>;
