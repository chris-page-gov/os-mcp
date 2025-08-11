import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { App } from './App';

// Basic smoke test to ensure primary panels render

describe('App layout', () => {
  it('renders tutorial, chat input, and output tabs', () => {
    render(<App />);
    // Tutorial heading
    expect(screen.getByText(/Tutorial/i)).toBeTruthy();
    // Chat placeholder
    expect(screen.getByPlaceholderText(/Ask a question/i)).toBeTruthy();
    // Output tab labels
    expect(screen.getByText('Answer')).toBeTruthy();
    expect(screen.getByText(/Map/)).toBeTruthy();
    expect(screen.getByText('Data')).toBeTruthy();
  });
});
