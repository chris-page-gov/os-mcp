import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  text: string;
  created: number;
}

export interface LayerMeta {
  id: string;
  name?: string;
  count?: number;
  added: number;
  geojson?: unknown; // stored raw parsed GeoJSON for rendering
  visible?: boolean;
}

export interface TraceEntry {
  id: string;
  ts: number;
  text: string;
  level?: 'info' | 'warn' | 'error';
}

export type OutputTab = 'answer' | 'map' | 'data';

interface ChatState {
  messages: ChatMessage[];
  layers: LayerMeta[];
  traces: TraceEntry[];
  activeTab: OutputTab;
  addMessage: (m: Omit<ChatMessage, 'id' | 'created'> & { id?: string }) => void;
  addLayer: (l: Omit<LayerMeta, 'added'> & { added?: number }) => void;
  toggleLayer: (id: string) => void;
  removeLayer: (id: string) => void;
  addTrace: (t: Omit<TraceEntry, 'id' | 'ts'> & { id?: string; ts?: number }) => void;
  updateMessage: (id: string, patch: Partial<ChatMessage>) => void;
  setActiveTab: (t: OutputTab) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  layers: [],
  traces: [],
  activeTab: 'answer',
  addMessage: (m) => set(s => ({ messages: [...s.messages, { id: m.id || crypto.randomUUID(), created: Date.now(), ...m }] })),
  addLayer: (l) => set(s => ({ layers: [...s.layers, { added: l.added || Date.now(), visible: l.visible ?? true, ...l }] })),
  toggleLayer: (id) => set(s => ({ layers: s.layers.map(l => l.id === id ? { ...l, visible: l.visible === false ? true : false } : l) })),
  removeLayer: (id) => set(s => ({ layers: s.layers.filter(l => l.id !== id) })),
  addTrace: (t) => set(s => ({ traces: [...s.traces.slice(-199), { id: t.id || crypto.randomUUID(), ts: t.ts || Date.now(), level: t.level || 'info', text: t.text }] })),
  updateMessage: (id, patch) => set(s => ({ messages: s.messages.map(m => m.id === id ? { ...m, ...patch } : m) })),
  setActiveTab: (t) => set({ activeTab: t })
}));
