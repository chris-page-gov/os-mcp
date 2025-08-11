import React from 'react';
import { useChatStore } from './store';

const PROMPTS = [
  'List collections',
  'Search buildings in Warwickshire',
  'Show me schools near Warwick',
  'Find rivers crossing Coventry',
];

export const TutorialPanel: React.FC = () => {
  const addMessage = useChatStore(s => s.addMessage);
  const traces = useChatStore(s => s.traces);
  return (
    <div style={{ padding: 12, fontSize: 13 }}>
      <h3 style={{ marginTop: 0 }}>Tutorial</h3>
      <p style={{ lineHeight: 1.3 }}>Try one of these starter prompts:</p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {PROMPTS.map(p => (
          <button
            key={p}
            style={{
              background: '#1b1f27',
              color: '#ddd',
              border: '1px solid #333',
              borderRadius: 16,
              padding: '4px 10px',
              cursor: 'pointer'
            }}
            onClick={() => addMessage({ role: 'user', text: p })}
          >
            {p}
          </button>
        ))}
      </div>
      <div style={{ marginTop: 18 }}>
        <details open>
          <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Trace (debug)</summary>
          <div style={{ maxHeight: 180, overflow: 'auto', fontFamily: 'monospace', fontSize: 11, marginTop: 6, border: '1px solid #222', padding: 6, background: '#12161d' }}>
            {traces.length === 0 && <div style={{ opacity: .6 }}>No trace entries yet.</div>}
            {traces.slice().reverse().map(t => (
              <div key={t.id} style={{ marginBottom: 4 }}>
                <span style={{ color: '#555' }}>{new Date(t.ts).toLocaleTimeString()} </span>
                <span style={{ color: t.level === 'error' ? '#f87171' : t.level === 'warn' ? '#fbbf24' : '#6ee7b7' }}>{t.level?.toUpperCase()}</span>
                <span style={{ color: '#ddd' }}> {t.text}</span>
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  );
};
