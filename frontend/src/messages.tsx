import React, { useState } from 'react';
import { useChatStore } from './store';
import { decideAction } from './lib/plan';
import { callMCPTool } from './lib/mcpClient';
import { detectGeoJSON } from './lib/geojson';

export const ChatWindow: React.FC = () => {
  const { messages, addMessage, addTrace, updateMessage, addLayer, setActiveTab } = useChatStore(s => ({ messages: s.messages, addMessage: s.addMessage, addTrace: s.addTrace, updateMessage: s.updateMessage, addLayer: s.addLayer, setActiveTab: s.setActiveTab }));
  const [text, setText] = useState('');

  const submit = () => {
    if (!text.trim()) return;
    const content = text.trim();
    const userId = crypto.randomUUID();
    addMessage({ id: userId, role: 'user', text: content });
    addTrace({ text: `User submitted: ${content}` });

    // Create placeholder assistant message we will stream into
    const assistantId = crypto.randomUUID();
    addMessage({ id: assistantId, role: 'assistant', text: '' });

    // Strategy:
    // 1. Attempt minimal heuristic: if prompt looks like a direct tool command (starts with 'list collections' etc.), call tool sequence.
    // 2. Else call chat tool if available (backend must expose /chat or we fallback).
    // Currently we only implement direct MCP tool invocation for a couple of patterns as PoC.
    (async () => {
      try {
        const action = decideAction(content);
        if (action.kind === 'tool') {
          await streamMCPTool({ name: action.name, arguments: action.args }, assistantId);
          return;
        }
        if (action.kind === 'planning') {
          await streamPlanningSearch({ assistantId });
          return;
        }
        addTrace({ text: 'Invoking chat tool (non-stream) fallback' });
        const chatResp = await callMCPTool('chat', { messages: [{ role: 'user', content }] }, { onTrace: e => addTrace(e) });
        updateMessage(assistantId, { text: chatResp });
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        updateMessage(assistantId, { text: `Error: ${msg}` });
        addTrace({ level: 'error', text: `Invocation failed: ${msg}` });
      }
    })();
    setText('');
  };

  async function streamPlanningSearch({ assistantId }: { assistantId: string }) {
    addTrace({ text: 'Heuristic planning search triggered (cinemas leamington)' });
    updateMessage(assistantId, { text: 'Planning workflow...\n' });
    // Step 1: get_workflow_context
  await callMCPTool('get_workflow_context', {});
    updateMessageAppend(assistantId, '\nGot workflow context. Fetching detailed collections...');
    // Step 2: fetch_detailed_collections (land use site)
    await callMCPTool('fetch_detailed_collections', { collection_ids: 'lus-fts-site-1' });
    updateMessageAppend(assistantId, '\nDetailed collection fetched. Searching cinemas...');
    // Step 3: search_features
    const result = await callMCPTool('search_features', { collection_id: 'lus-fts-site-1', limit: 5, filter: "oslandusetertiarygroup = 'Cinema'" });
    updateMessageAppend(assistantId, '\nSearch complete. Showing results:\n' + result);
  }

  function updateMessageAppend(id: string, addition: string) {
    const msg = messages.find(m => m.id === id);
    const current = msg?.text || '';
    updateMessage(id, { text: current + addition });
  }

  interface ToolCall { name: string; arguments: Record<string, unknown>; }
  async function streamMCPTool(toolCall: ToolCall, assistantId: string) {
    addTrace({ text: `Calling MCP tool: ${toolCall.name}` });
    const output = await callMCPTool(toolCall.name, toolCall.arguments, { onTrace: e => addTrace(e) });
    updateMessage(assistantId, { text: output });
    const detection = detectGeoJSON(output);
    if (detection.isGeoJSON) {
      const layerId = `${toolCall.name}-${Date.now()}`;
      addLayer({ id: layerId, name: toolCall.name, count: detection.featureCount, geojson: detection.parsed });
      addTrace({ text: `Detected GeoJSON (${detection.featureCount || 1} feature(s)) -> layer ${layerId}` });
      setActiveTab('map');
    }
  }

  // inline HTTP client removed; logic in lib/mcpClient for unit tests

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {messages.map(m => (
          <div key={m.id} style={{ marginBottom: 14, fontSize: 13 }}>
            <div style={{ opacity: .7, fontSize: 11, textTransform: 'uppercase', letterSpacing: .5 }}>{m.role}</div>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.35 }}>{m.text}</div>
          </div>
        ))}
      </div>
      <div style={{ padding: 12, borderTop: '1px solid #222', display: 'flex', gap: 8 }}>
        <input value={text} onChange={e => setText(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } }} placeholder="Ask a question about NGD..." style={{ flex: 1, background: '#1b1f27', border: '1px solid #333', color: '#eee', borderRadius: 6, padding: '8px 10px', fontSize: 13 }} />
        <button onClick={submit} style={{ background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 14px', cursor: 'pointer', fontSize: 13 }}>Send</button>
      </div>
    </div>
  );
};
