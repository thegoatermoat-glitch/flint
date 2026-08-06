// Minimal zero-dependency static file server for the Flint site.
// Used only to host frontend/public locally (port 3000). The site itself is
// pure static and can be deployed to Vercel/Netlify/etc without this server.
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "public");
const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || "0.0.0.0";

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".mjs": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".wasm": "application/wasm",
  ".ico": "image/x-icon",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".txt": "text/plain; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".mp3": "audio/mpeg",
  ".wav": "audio/wav",
  ".md": "text/plain; charset=utf-8",
};

function send(res, status, body, headers = {}) {
  res.writeHead(status, headers);
  res.end(body);
}

function serveFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const type = MIME[ext] || "application/octet-stream";
  const headers = { "Content-Type": type };
  // Service worker must be allowed to control the whole origin.
  if (path.basename(filePath) === "sw.js") {
    headers["Cache-Control"] = "no-cache";
    headers["Service-Worker-Allowed"] = "/";
  }
  const stream = fs.createReadStream(filePath);
  stream.on("open", () => res.writeHead(200, headers));
  stream.on("error", () => send(res, 500, "Internal Server Error"));
  stream.pipe(res);
}

const server = http.createServer((req, res) => {
  let urlPath;
  try {
    urlPath = decodeURIComponent(new URL(req.url, "http://x").pathname);
  } catch {
    return send(res, 400, "Bad Request");
  }

  // Resolve within ROOT, block traversal.
  let target = path.normalize(path.join(ROOT, urlPath));
  if (!target.startsWith(ROOT)) return send(res, 403, "Forbidden");

  fs.stat(target, (err, stat) => {
    if (!err && stat.isDirectory()) target = path.join(target, "index.html");

    fs.stat(target, (err2, stat2) => {
      if (err2 || !stat2.isFile()) {
        // Fallback to the site's own 404 page.
        const notFound = path.join(ROOT, "404.html");
        return fs.readFile(notFound, (e, buf) =>
          e
            ? send(res, 404, "Not Found")
            : send(res, 404, buf, { "Content-Type": "text/html; charset=utf-8" })
        );
      }
      serveFile(res, target);
    });
  });
});

server.listen(PORT, HOST, () => {
  console.log(`Flint static server running at http://${HOST}:${PORT}`);
});
