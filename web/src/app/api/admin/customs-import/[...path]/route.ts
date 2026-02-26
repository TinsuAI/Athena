/**
 * Streaming proxy for customs import file uploads.
 *
 * Next.js rewrite proxy buffers the entire request body in memory,
 * which causes ECONNRESET for large files (30MB+). This route handler
 * streams the multipart body directly to FastAPI without buffering.
 *
 * Matched paths: /api/admin/customs-import/upload, /execute, /history, /stats
 */

const API_BACKEND_URL =
  process.env.API_BACKEND_URL || "http://localhost:8980";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const targetPath = `/api/admin/customs-import/${path.join("/")}`;
  const targetUrl = `${API_BACKEND_URL}${targetPath}`;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const cookie = request.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);

  const response = await fetch(targetUrl, {
    method: "POST",
    headers,
    body: request.body,
    // @ts-expect-error -- duplex required for streaming request bodies in Node.js
    duplex: "half",
  });

  return new Response(response.body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") || "application/json",
    },
  });
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const targetPath = `/api/admin/customs-import/${path.join("/")}`;
  const url = new URL(request.url);
  const targetUrl = `${API_BACKEND_URL}${targetPath}${url.search}`;

  const headers = new Headers();
  const cookie = request.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);

  const response = await fetch(targetUrl, {
    method: "GET",
    headers,
  });

  return new Response(response.body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") || "application/json",
    },
  });
}
