import { describe, it, expect } from 'vitest';
import { detectGeoJSON } from './geojson';

describe('detectGeoJSON', () => {
  it('detects FeatureCollection', () => {
    const sample = JSON.stringify({ type: 'FeatureCollection', features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [0,0] }, properties: {} }] });
    const d = detectGeoJSON(sample);
    expect(d.isGeoJSON).toBe(true);
    expect(d.featureCount).toBe(1);
  });
  it('rejects invalid JSON', () => {
    expect(detectGeoJSON('{bad json').isGeoJSON).toBe(false);
  });
  it('detects geometry only', () => {
    const d = detectGeoJSON(JSON.stringify({ type: 'Point', coordinates: [0,0] }));
    expect(d.isGeoJSON).toBe(true);
    expect(d.featureCount).toBe(1);
  });
});
