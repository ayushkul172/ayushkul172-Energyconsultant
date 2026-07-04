import { useState, useEffect, useCallback } from 'react';

type Theme = 'dark' | 'light';

interface UseThemeReturn {
  theme: Theme;
  toggleTheme: () => void;
  isDark: boolean;
}

const STORAGE_KEY = 'theme';
const TRANSITION_DURATION = 400;

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'dark';
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'dark' || stored === 'light') return stored;
  return 'dark';
}

export function useTheme(): UseThemeReturn {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  // Apply theme class to document root on mount and theme change
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('dark', 'light');
    root.classList.add(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    const root = document.documentElement;

    // Add transitioning class to enable smooth CSS transitions
    root.classList.add('theme-transitioning');

    // Swap theme
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));

    // Remove transitioning class after transition completes
    setTimeout(() => {
      root.classList.remove('theme-transitioning');
    }, TRANSITION_DURATION);
  }, []);

  return {
    theme,
    toggleTheme,
    isDark: theme === 'dark',
  };
}
