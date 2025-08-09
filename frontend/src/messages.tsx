import React, { useState } from 'react';
import { useChatStore } from './store';

export const ChatWindow: React.FC = () => {
  const { messages, addMessage } = useChatStore(s => ({ messages: s.messages, addMessage: s.addMessage }));
  const [text, setText] = useState('');

  const submit = () => {
    if (!text.trim()) return;
    addMessage({ role: 'user', text: text.trim() });
    setText('');
  };

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
