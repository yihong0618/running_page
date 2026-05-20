import { useState, useEffect, useCallback, useSyncExternalStore } from 'react';
import { MAP_TILE_STYLE_LIGHT, MAP_TILE_STYLE_DARK } from '@/utils/const';

export type Theme = 'light' | 'dark';

// Custom event name for theme changes
export const THEME_CHANGE_EVENT = 'theme-change';

const getCurrentThemeSnapshot = () => {
  if (typeof window === 'undefined') return 'dark';
  return (
    document.documentElement.getAttribute('data-theme') ||
    localStorage.getItem('theme') ||
    'dark'
  );
};

const subscribeToThemeChanges = (onStoreChange: () => void) => {
  if (typeof window === 'undefined') return () => {};

  const observer = new MutationObserver((mutations) => {
    if (
      mutations.some(
        (mutation) =>
          mutation.type === 'attributes' &&
          mutation.attributeName === 'data-theme'
      )
    ) {
      onStoreChange();
    }
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  });

  const handleThemeChange = () => onStoreChange();
  const handleStorageChange = (e: StorageEvent) => {
    if (e.key === 'theme') {
      onStoreChange();
    }
  };

  window.addEventListener(THEME_CHANGE_EVENT, handleThemeChange);
  window.addEventListener('storage', handleStorageChange);

  return () => {
    observer.disconnect();
    window.removeEventListener(THEME_CHANGE_EVENT, handleThemeChange);
    window.removeEventListener('storage', handleStorageChange);
  };
};

/**
 * Converts a theme value to the corresponding map style
 * @param theme - The current theme ('light' or 'dark')
 * @returns The appropriate map style for the theme
 */
export const getMapThemeFromCurrentTheme = (theme: Theme): string => {
  if (theme === 'dark') return MAP_TILE_STYLE_DARK;
  return MAP_TILE_STYLE_LIGHT;
};

/**
 * Hook for managing map theme based on application theme
 * @returns The current map theme style
 */
export const useMapTheme = () => {
  const themeSnapshot = useSyncExternalStore(
    subscribeToThemeChanges,
    getCurrentThemeSnapshot,
    () => 'dark'
  );

  return getMapThemeFromCurrentTheme(
    themeSnapshot === 'light' ? 'light' : 'dark'
  );
};

/**
 * Main theme hook for the application
 * @returns Object with current theme and function to change theme
 */
export const useTheme = () => {
  // Initialize theme from localStorage or default to dark
  const [themeState, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'dark';
    return (localStorage.getItem('theme') as Theme) || 'dark';
  });

  /**
   * Set theme and dispatch event to notify other components
   */
  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);

    // Dispatch custom event for theme change
    const event = new CustomEvent(THEME_CHANGE_EVENT, {
      detail: { theme: newTheme },
    });
    window.dispatchEvent(event);
  }, []);

  // Apply theme changes to DOM and localStorage
  useEffect(() => {
    const root = window.document.documentElement;

    // Set attribute and save to localStorage for both themes
    root.setAttribute('data-theme', themeState);
    localStorage.setItem('theme', themeState);
  }, [themeState]);

  return {
    theme: themeState,
    setTheme,
  };
};

/**
 * Hook to trigger re-render when theme changes for dynamic color calculations
 * @returns A counter that increments when theme changes
 */
export const useThemeChangeCounter = () => {
  return useSyncExternalStore(
    subscribeToThemeChanges,
    getCurrentThemeSnapshot,
    () => 'dark'
  );
};
