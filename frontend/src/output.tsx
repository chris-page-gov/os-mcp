import React, { useEffect, useRef } from 'react';
import { useChatStore, ChatMessage, LayerMeta } from './store';
import L from 'leaflet';

export const OutputPanel: React.FC = () => {
  const { activeTab, setActiveTab, messages, layers } = useChatStore((s) => ({
    activeTab: s.activeTab, setActiveTab: s.setActiveTab, messages: s.messages, layers: s.layers
  }));
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (activeTab === 'map' && !mapRef.current) {
      mapRef.current = L.map('map').setView([52.28, -1.53], 12);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OSM contributors'
      }).addTo(mapRef.current);
    }
  }, [activeTab]);

  const assistantMessages: ChatMessage[] = messages.filter((m: ChatMessage) => m.role !== 'user').slice(-10);

  return (
    <>
      <div className="tab-bar">
        <div className={"tab " + (activeTab==='answer'?'active':'')} onClick={() => setActiveTab('answer')}>Answer</div>
        <div className={"tab " + (activeTab==='map'?'active':'')} onClick={() => setActiveTab('map')}>Map ({layers.length})</div>
        <div className={"tab " + (activeTab==='data'?'active':'')} onClick={() => setActiveTab('data')}>Data</div>
      </div>
      {activeTab === 'answer' && (
        <div style={{ padding: 12, overflow:'auto', flex:1 }}>
          {assistantMessages.map((m: ChatMessage) => (
            <div key={m.id} style={{ marginBottom: 12, fontSize:13 }}>
              <strong style={{ color: m.role === 'assistant' ? '#8fe388' : '#ffaa33' }}>{m.role}</strong>
              <div style={{ whiteSpace:'pre-wrap' }}>{m.text}</div>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'map' && <div className="map-container"><div id="map" /></div>}
      {activeTab === 'data' && (
        <div style={{ padding:12, fontSize:12 }}>
          <h4>Layers</h4>
          {layers.map((l: LayerMeta) => <div key={l.id} className="layer-toggle">{l.id} {l.count ? `(${l.count})` : ''}</div>)}
        </div>
      )}
    </>
  );
};
