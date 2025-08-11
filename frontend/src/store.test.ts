import { describe, it, expect } from 'vitest';
import { useChatStore } from './store';

function reset() { useChatStore.setState({ messages: [], layers: [], traces: [], activeTab: 'answer' }); }

describe('chat store', () => {
  it('adds & updates message', () => {
    reset();
    useChatStore.getState().addMessage({ role: 'user', text: 'Hi' });
    const id = useChatStore.getState().messages[0].id;
    useChatStore.getState().updateMessage(id, { text: 'Hello' });
    expect(useChatStore.getState().messages[0].text).toBe('Hello');
  });
  it('keeps only last 200 traces', () => {
    reset();
    for (let i = 0; i < 205; i++) useChatStore.getState().addTrace({ text: 't' + i });
    const traces = useChatStore.getState().traces;
    expect(traces.length).toBe(200);
    expect(traces[0].text).toBe('t5');
  });
  it('toggles and removes layers', () => {
    reset();
    useChatStore.getState().addLayer({ id: 'L1', name: 'Layer1' });
    expect(useChatStore.getState().layers[0].visible).toBe(true);
    (useChatStore.getState() as any).toggleLayer('L1');
    expect(useChatStore.getState().layers[0].visible).toBe(false);
    (useChatStore.getState() as any).removeLayer('L1');
    expect(useChatStore.getState().layers.length).toBe(0);
  });
});
