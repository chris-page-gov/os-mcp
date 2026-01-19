export type PlannedAction =
  | { kind: 'tool'; name: string; args: Record<string, unknown> }
  | { kind: 'planning'; scenario: 'cinemaSearch'; town: string }
  | { kind: 'chat' };

// Pure heuristic decision function for unit tests
export function decideAction(prompt: string): PlannedAction {
  const p = prompt.trim();
  if (!p) return { kind: 'chat' };
  if (/^list collections/i.test(p)) return { kind: 'tool', name: 'os_ngd_list_mapping_collections', args: {} };
  if (/cinema/i.test(p) && /leamington/i.test(p)) return { kind: 'planning', scenario: 'cinemaSearch', town: 'Leamington' };
  return { kind: 'chat' };
}
