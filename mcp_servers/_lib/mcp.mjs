// Minimal MCP stdio JSON-RPC handler. One per domain server imports this.

export function runServer({ name, tools, handlers }) {
  const toolList = Object.entries(tools).map(([n, t]) => ({ name: n, ...t }));

  async function handle(req) {
    const { jsonrpc, id, method, params } = req;
    try {
      if (method === 'initialize') {
        return { jsonrpc, id, result: { protocolVersion: '2024-11-05', capabilities: { tools: {} }, serverInfo: { name, version: '1.0.0' } } };
      }
      if (method === 'tools/list') {
        return { jsonrpc, id, result: { tools: toolList } };
      }
      if (method === 'tools/call') {
        const fn = handlers[params.name];
        if (!fn) throw new Error(`Unknown tool: ${params.name}`);
        const result = await fn(params.arguments || {});
        return { jsonrpc, id, result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] } };
      }
      return { jsonrpc, id, error: { code: -32601, message: 'Method not found' } };
    } catch (e) {
      return { jsonrpc, id, error: { code: -32603, message: e.message } };
    }
  }

  let buf = '';
  process.stdin.on('data', async (chunk) => {
    buf += chunk.toString();
    let idx;
    while ((idx = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 1);
      if (!line) continue;
      try {
        const req = JSON.parse(line);
        const res = await handle(req);
        process.stdout.write(JSON.stringify(res) + '\n');
      } catch (e) {
        console.error(`[${name}] parse error:`, e.message);
      }
    }
  });
  console.error(`[${name}] MCP server ready`);
}
