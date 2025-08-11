import React, { useEffect, useRef } from 'react';
// Helper to safely add GeoJSON without leaking any outside
function addGeoJSON(map: L.Map, data: unknown, name: string) {
  try {
    // Internal cast only; leaflet types not imported fully here
    (L as unknown as { geoJSON: (d: unknown, o?: { onEachFeature?: (f: unknown, layer: unknown) => void }) => L.LayerGroup })
      .geoJSON(data, { onEachFeature: (_f: unknown, layer: unknown) => { (layer as { bindPopup?: (s: string) => void }).bindPopup?.(name); } })
      .addTo(map);
  } catch {
    /* ignore */
  }
}
import { useChatStore, ChatMessage, LayerMeta } from './store';
import L from 'leaflet';

export const OutputPanel: React.FC = () => {
  const { activeTab, setActiveTab, messages, layers, toggleLayer, removeLayer } = useChatStore((s) => ({
    activeTab: s.activeTab,
    setActiveTab: s.setActiveTab,
    messages: s.messages,
    layers: s.layers,
    toggleLayer: s.toggleLayer,
    removeLayer: s.removeLayer
  }));
  const mapRef = useRef<L.Map | null>(null);

  const addedLayerIdsRef = useRef<Set<string>>(new Set());
  const leafletLayerRef = useRef<Map<string, L.LayerGroup>>(new Map());

  useEffect(() => {
    if (activeTab === 'map' && !mapRef.current) {
      mapRef.current = L.map('map').setView([52.28, -1.53], 12);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OSM contributors'
      }).addTo(mapRef.current);
    }
    // Sync geojson layers with store state when on map tab
    if (activeTab === 'map' && mapRef.current) {
      // Remove stale layers
      leafletLayerRef.current.forEach((layer, id) => {
        if (!layers.find(l => l.id === id && l.visible !== false)) {
          mapRef.current!.removeLayer(layer);
          leafletLayerRef.current.delete(id);
          addedLayerIdsRef.current.delete(id);
        }
      });
      // Add any missing visible layers
      layers.forEach(l => {
        if (l.geojson && l.visible !== false && !leafletLayerRef.current.get(l.id)) {
          addGeoJSON(mapRef.current!, l.geojson, l.name || l.id);
          // capture reference (last added layer)
          let captured: L.LayerGroup | undefined;
          mapRef.current!.eachLayer(layer => {
            const existingLayers = Array.from(leafletLayerRef.current.values());
            if (!existingLayers.includes(layer as unknown as L.LayerGroup)) {
              captured = layer as L.LayerGroup;
            }
          });
          if (captured) leafletLayerRef.current.set(l.id, captured);
          addedLayerIdsRef.current.add(l.id);
        }
      });
    }
  }, [activeTab, layers]);

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
          {layers.length === 0 && <div style={{ opacity:.7 }}>No layers yet.</div>}
          {layers.map((l: LayerMeta) => (
            <div key={l.id} style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4 }}>
              <input type="checkbox" checked={l.visible !== false} onChange={() => toggleLayer(l.id)} aria-label={`toggle-${l.id}`} />
              <span style={{ flex:1 }}>{l.name || l.id} {l.count!==undefined && `( ${l.count} )`}</span>
              <button onClick={() => removeLayer(l.id)} aria-label={`remove-${l.id}`} style={{ background:'transparent', border:'1px solid #444', color:'#aaa', fontSize:10, padding:'2px 6px', cursor:'pointer' }}>x</button>
            </div>
          ))}
        </div>
      )}
    </>
  );
};
