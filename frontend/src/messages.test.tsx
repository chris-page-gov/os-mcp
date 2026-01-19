import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import { ChatWindow } from './messages';
import { useChatStore } from './store';

function resetStore() { useChatStore.setState({ messages: [], layers: [], traces: [], activeTab: 'answer' }); }

vi.mock('./lib/mcpClient', () => ({ callMCPTool: vi.fn() }));
import { callMCPTool } from './lib/mcpClient';
type CallMock = { mock: { calls: unknown[][] }; mockResolvedValueOnce: (v: unknown) => CallMock };

beforeEach(() => { resetStore(); vi.clearAllMocks(); });

async function submit(text: string) {
  const inputs = screen.getAllByPlaceholderText(/Ask a question/i);
  const el = inputs[0];
  fireEvent.change(el, { target: { value: text } });
  fireEvent.keyDown(el, { key: 'Enter', code: 'Enter' });
}

describe('ChatWindow heuristics', () => {
  it('calls os_ngd_list_mapping_collections tool for prompt', async () => {
  (callMCPTool as unknown as CallMock).mockResolvedValueOnce('COLLS');
    render(<ChatWindow />);
    await submit('List collections');
    await waitFor(() => {
      const msgs = useChatStore.getState().messages;
      expect(msgs.some(m => m.role === 'assistant' && m.text.includes('COLLS'))).toBe(true);
    });
  expect((callMCPTool as unknown as CallMock).mock.calls[0][0]).toBe('os_ngd_list_mapping_collections');
  });

  it('runs planning workflow for cinema search', async () => {
  (callMCPTool as unknown as CallMock)
      .mockResolvedValueOnce('CTX')
      .mockResolvedValueOnce('DETAIL')
      .mockResolvedValueOnce('RESULTS');
    render(<ChatWindow />);
    await submit('Find a cinema in Leamington');
    await waitFor(() => {
      const assistant = useChatStore.getState().messages.find(m => m.role === 'assistant');
      expect(assistant?.text).toMatch(/Search complete/);
      expect(assistant?.text).toMatch(/RESULTS/);
    });
  expect((callMCPTool as unknown as CallMock).mock.calls.length).toBe(3);
  });

  it('falls back to chat tool', async () => {
  (callMCPTool as unknown as CallMock).mockResolvedValueOnce('Chat answer');
    render(<ChatWindow />);
    await submit('Explain roads dataset');
    await waitFor(() => {
      const assistant = useChatStore.getState().messages.find(m => m.role === 'assistant');
      expect(assistant?.text).toContain('Chat answer');
    });
  expect((callMCPTool as unknown as CallMock).mock.calls[0][0]).toBe('chat');
  });

  it('auto-detects GeoJSON and adds a layer', async () => {
    const fc = JSON.stringify({ type: 'FeatureCollection', features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [1,2] }, properties: {} }] });
    (callMCPTool as unknown as CallMock).mockResolvedValueOnce(fc);
    render(<ChatWindow />);
    await submit('List collections');
    await waitFor(() => {
      const layers = useChatStore.getState().layers;
      expect(layers.length).toBe(1);
  expect(layers[0].count).toBe(1);
  expect(layers[0].geojson).toBeTruthy();
    });
  });
});
