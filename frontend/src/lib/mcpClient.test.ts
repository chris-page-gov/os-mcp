import { describe, it, expect, vi } from 'vitest';
import { callMCPTool } from './mcpClient';

function mf(json: unknown, status = 200) {
  return vi.fn().mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => json });
}

describe('callMCPTool', () => {
  it('returns nested text', async () => {
    const txt = await callMCPTool('x', {}, { fetchImpl: mf({ result: { content: [{ text: 'hi' }] } }) });
    expect(txt).toBe('hi');
  });
  it('stringifies fallback', async () => {
    const txt = await callMCPTool('x', {}, { fetchImpl: mf({ result: {} }) });
    expect(txt).toMatch(/result/);
  });
  it('401 error', async () => {
    await expect(callMCPTool('x', {}, { fetchImpl: mf({}, 401) })).rejects.toThrow(/401/);
  });
  it('403 error', async () => {
    await expect(callMCPTool('x', {}, { fetchImpl: mf({}, 403) })).rejects.toThrow(/403/);
  });
  it('500 error', async () => {
    await expect(callMCPTool('x', {}, { fetchImpl: mf({}, 500) })).rejects.toThrow(/500/);
  });
});
