// Minimal ambient fetch type (browser / jsdom provides it in runtime tests)
// Generic minimal fetch signature (avoids depending on DOM lib types in isolated unit tests)
type FetchLike = (input: unknown, init?: unknown) => Promise<{
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
}>;

export interface MCPClientOptions {
  endpoint?: string;
  token?: string;
  fetchImpl?: FetchLike;
  onTrace?: (e: { level?: 'info' | 'warn' | 'error'; text: string }) => void;
}

export async function callMCPTool(
  name: string,
  args: Record<string, unknown>,
  opts: MCPClientOptions = {}
): Promise<string> {
  const g = globalThis as unknown as { MCP_HTTP_URL?: string; MCP_TOKEN?: string; fetch?: FetchLike };
  const {
    endpoint = g.MCP_HTTP_URL || 'http://127.0.0.1:8000/mcp',
    token = g.MCP_TOKEN || 'dev-token',
    fetchImpl = g.fetch || (async () => { throw new Error('fetch not available'); }) as FetchLike,
    onTrace
  } = opts;
  const body = { jsonrpc: '2.0', id: crypto.randomUUID(), method: 'tools/call', params: { name, arguments: args } };
  const res = await fetchImpl(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(body)
  });
  if (res.status === 401) { onTrace?.({ level: 'error', text: '401 Unauthorized' }); throw new Error('HTTP 401'); }
  if (res.status === 403) { onTrace?.({ level: 'error', text: '403 Forbidden' }); throw new Error('HTTP 403'); }
  if (!res.ok) { const msg = `HTTP ${res.status}`; onTrace?.({ level: 'error', text: msg }); throw new Error(msg); }
  let json: unknown; try { json = await res.json(); } catch { onTrace?.({ level: 'error', text: 'Invalid JSON response' }); throw new Error('Invalid JSON'); }
  // Narrow structure defensively
  // Dynamic JSON-RPC structure; narrow at runtime only
  const text = (json as { result?: { content?: Array<{ text?: string }> } })?.result?.content?.[0]?.text || JSON.stringify(json);
  onTrace?.({ text: `Tool ${name} OK (${text.length} chars)` });
  return text;
}
