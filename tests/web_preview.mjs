// Serve the production bundle for local smoke/visual checks, using only Node built-ins.
// API requests go to the isolated test Go process started by tests.web_smoke.
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../VPNSite/dist/', import.meta.url));
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' };
http.createServer(async (req, res) => {
  if (req.url.startsWith('/api/')) {
    const upstream = http.request({ hostname: '127.0.0.1', port: 8081, path: req.url, method: req.method, headers: req.headers }, response => {
      res.writeHead(response.statusCode, response.headers); response.pipe(res);
    });
    upstream.on('error', () => { res.writeHead(503, { 'Content-Type': 'application/json' }); res.end('{"error":"Тестовый API ещё не запущен"}'); });
    req.pipe(upstream); return;
  }
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const path = resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!path.startsWith(root)) { res.writeHead(403); res.end(); return; }
    const content = await readFile(path);
    res.writeHead(200, { 'Content-Type': types[extname(path)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(content);
  } catch { res.writeHead(404); res.end('Not found'); }
}).listen(5173, '127.0.0.1', () => console.log('Production bundle preview: http://localhost:5173'));
