/**
 * ProjeX Collab Server — Yjs WebSocket for real-time collaboration (port 8400).
 */
const http = require("http");
const { setupWSConnection } = require("y-websocket/bin/utils");
const WebSocket = require("ws");

const PORT = process.env.PORT || 8400;

const server = http.createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "healthy", service: "collab-server" }));
    return;
  }
  res.writeHead(404);
  res.end();
});

const wss = new WebSocket.Server({ server });

wss.on("connection", (ws, req) => {
  setupWSConnection(ws, req);
});

server.listen(PORT, () => {
  console.log(`Collab server listening on port ${PORT}`);
});
