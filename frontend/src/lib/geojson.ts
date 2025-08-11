export interface GeoJSONDetection { isGeoJSON: boolean; featureCount?: number; type?: string; parsed?: unknown; }

export function detectGeoJSON(input: string | unknown): GeoJSONDetection {
  let obj: unknown = input;
  if (typeof input === 'string') {
    if (input.length > 500000) return { isGeoJSON: false };
    try { obj = JSON.parse(input); } catch { return { isGeoJSON: false }; }
  }
  if (!obj || typeof obj !== 'object') return { isGeoJSON: false };
  const rec = obj as { type?: string; features?: unknown[]; geometry?: unknown };
  const t = rec.type;
  if (t === 'FeatureCollection' && Array.isArray(rec.features)) {
    return { isGeoJSON: true, featureCount: rec.features.length, type: t, parsed: obj };
  }
  if (t === 'Feature' && (rec as { geometry?: unknown }).geometry) return { isGeoJSON: true, featureCount: 1, type: t, parsed: obj };
  if (t && ['Point','MultiPoint','LineString','MultiLineString','Polygon','MultiPolygon','GeometryCollection'].includes(t)) {
    return { isGeoJSON: true, featureCount: 1, type: t, parsed: obj };
  }
  return { isGeoJSON: false };
}
