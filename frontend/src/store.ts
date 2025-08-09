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
}

export type OutputTab = 'answer' | 'map' | 'data';

interface ChatState {
  messages: ChatMessage[];
  layers: LayerMeta[];
  activeTab: OutputTab;
  addMessage: (m: Omit<ChatMessage, 'id' | 'created'> & { id?: string }) => void;
  addLayer: (l: Omit<LayerMeta, 'added'> & { added?: number }) => void;
  setActiveTab: (t: OutputTab) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  layers: [],
  activeTab: 'answer',
  addMessage: (m) => set(s => ({ messages: [...s.messages, { id: m.id || crypto.randomUUID(), created: Date.now(), ...m }] })),
  addLayer: (l) => set(s => ({ layers: [...s.layers, { added: l.added || Date.now(), ...l }] })),
  setActiveTab: (t) => set({ activeTab: t })
}));
