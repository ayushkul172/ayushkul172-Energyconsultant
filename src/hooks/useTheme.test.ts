import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';

describe('useTheme', () => {
  let storage: Record<string, string>;

  beforeEach(() => {
    storage = {};

    const localStorageMock = {
      getItem: vi.fn((key: string) => storage[key] ?? null),
      setItem: vi.fn((key: string, value: string) => { storage[key] = value; }),
      removeItem: vi.fn((key: string) => { delete storage[key]; }),
      clear: vi.fn(() => { storage = {}; }),
      length: 0,
      key: vi.fn(() => null),
    };

    vi.stubGlobal('localStorage', localStorageMock);
    document.documentElement.classList.remove('dark', 'light', 'theme-transitioning');
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('should default to dark theme when no stored preference', () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('should initialize from localStorage', () => {
    storage['theme'] = 'light';
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe('light');
    expect(result.current.isDark).toBe(false);
    expect(document.documentElement.classList.contains('light')).toBe(true);
  });

  it('should toggle from dark to light', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('light');
    expect(result.current.isDark).toBe(false);
    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(storage['theme']).toBe('light');
  });

  it('should toggle from light to dark', () => {
    storage['theme'] = 'light';
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
  });

  it('should add theme-transitioning class during toggle', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);
  });

  it('should remove theme-transitioning class after 400ms', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(true);

    act(() => {
      vi.advanceTimersByTime(400);
    });

    expect(document.documentElement.classList.contains('theme-transitioning')).toBe(false);
  });

  it('should persist theme choice to localStorage', () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(storage['theme']).toBe('light');

    act(() => {
      result.current.toggleTheme();
    });

    expect(storage['theme']).toBe('dark');
  });

  it('should default to dark when localStorage has invalid value', () => {
    storage['theme'] = 'invalid';
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe('dark');
  });
});
