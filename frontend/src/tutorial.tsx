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
    </div>
  );
};
