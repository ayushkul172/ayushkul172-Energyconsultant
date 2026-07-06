import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useReducedMotion } from './useReducedMotion';

describe('useReducedMotion', () => {
  let listeners: Map<string, (event: MediaQueryListEvent) => void>;
  let matchesMock: boolean;

  beforeEach(() => {
    listeners = new Map();
    matchesMock = false;

    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: matchesMock,
        media: query,
        addEventListener: (_event: string, handler: (event: MediaQueryListEvent) => void) => {
          listeners.set('change', handler);
        },
        removeEventListener: (_event: string) => {
          listeners.delete('change');
        },
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it('should return false when no reduced motion preference', () => {
    matchesMock = false;
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);
  });

  it('should return true when reduced motion is preferred', () => {
    matchesMock = true;
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(true);
  });

  it('should update when system preference changes', () => {
    matchesMock = false;
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);

    // Simulate system preference change
    const handler = listeners.get('change');
    expect(handler).toBeDefined();

    act(() => {
      handler!({ matches: true } as MediaQueryListEvent);
    });

    expect(result.current).toBe(true);
  });

  it('should clean up event listener on unmount', () => {
    matchesMock = false;
    const { unmount } = renderHook(() => useReducedMotion());

    expect(listeners.has('change')).toBe(true);

    unmount();

    expect(listeners.has('change')).toBe(false);
  });
});
