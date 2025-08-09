import React from 'react';
import { createRoot } from 'react-dom/client';
import { TutorialPanel } from './tutorial';
import { ChatWindow } from './messages';
import { OutputPanel } from './output';

const App: React.FC = () => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr 400px', height: '100vh', fontFamily: 'system-ui, sans-serif', background:'#0e1116', color:'#e6e6e6' }}>
      <div style={{ borderRight: '1px solid #222', overflow:'auto' }}>
        <TutorialPanel />
      </div>
      <div style={{ display:'flex', flexDirection:'column', overflow:'hidden' }}>
        <ChatWindow />
      </div>
      <div style={{ borderLeft:'1px solid #222', display:'flex', flexDirection:'column' }}>
        <OutputPanel />
      </div>
    </div>
  );
};

createRoot(document.getElementById('root')!).render(<App />);
