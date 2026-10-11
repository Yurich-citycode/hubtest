#!/usr/bin/env node
/**
 * Прокси к превью-студии HyperFrames.
 *
 * Зачем: `hyperframes preview` жёстко слушает 127.0.0.1, а живое превью в Arena
 * открывается только с адреса вида 0.0.0.0:порт. Этот прокси слушает 0.0.0.0 и
 * прозрачно пересылает запросы (включая WebSocket-обновления) на студию внутри
 * песочницы, поэтому браузеру не нужны никакие localhost-адреса.
 *
 * Запуск:  node bin/preview-proxy.mjs [--port 3100] [--target 3002]
 */
import http from 'node:http';
import net from 'node:net';

const args = process.argv.slice(2);
const getArg = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? Number(args[i + 1]) : fallback;
};

const PORT = getArg('port', 3100);
const TARGET_PORT = getArg('target', 3002);
const TARGET_HOST = '127.0.0.1';

const log = (...a) => console.log('[preview-proxy]', ...a);

const server = http.createServer((req, res) => {
  const upstream = http.request(
    {
      host: TARGET_HOST,
      port: TARGET_PORT,
      method: req.method,
      path: req.url,
      headers: { ...req.headers, host: `${TARGET_HOST}:${TARGET_PORT}` },
    },
    (upRes) => {
      res.writeHead(upRes.statusCode || 502, upRes.headers);
      upRes.pipe(res);
    },
  );

  upstream.on('error', (err) => {
    log('ошибка апстрима:', err.message);
    if (!res.headersSent) res.writeHead(502, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('Студия не отвечает. Запусти: bash bin/hf.sh preview projects/<name> --foreground --no-open');
  });

  req.pipe(upstream);
});

// WebSocket и HMR: студия обновляет кадр по сокету
server.on('upgrade', (req, socket, head) => {
  const upstream = net.connect(TARGET_PORT, TARGET_HOST, () => {
    const headers = Object.entries({ ...req.headers, host: `${TARGET_HOST}:${TARGET_PORT}` })
      .map(([k, v]) => `${k}: ${v}`)
      .join('\r\n');
    upstream.write(`${req.method} ${req.url} HTTP/1.1\r\n${headers}\r\n\r\n`);
    if (head && head.length) upstream.write(head);
    upstream.pipe(socket);
    socket.pipe(upstream);
  });

  const fail = (err) => {
    log('сокет закрыт:', err?.message ?? '');
    socket.destroy();
  };
  upstream.on('error', fail);
  socket.on('error', fail);
});

server.listen(PORT, '0.0.0.0', () => {
  log(`слушаю 0.0.0.0:${PORT} → студия на ${TARGET_HOST}:${TARGET_PORT}`);
});
