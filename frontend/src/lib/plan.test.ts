import { describe, it, expect } from 'vitest';
import { decideAction } from './plan';

describe('decideAction', () => {
  it('detects list collections', () => {
    expect(decideAction('List collections')).toEqual({ kind: 'tool', name: 'list_collections', args: {} });
  });
  it('detects cinema search heuristic', () => {
    const a = decideAction('show me a cinema in leamington');
    expect(a.kind).toBe('planning');
  });
  it('falls back to chat', () => {
    expect(decideAction('Tell me about rivers').kind).toBe('chat');
  });
  it('empty falls back', () => {
    expect(decideAction('   ').kind).toBe('chat');
  });
});
