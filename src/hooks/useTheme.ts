import { useState, useEffect, useCallback } from 'react';
import { MAP_TILE_STYLE_LIGHT, MAP_TILE_STYLE_DARK } from '@/utils/const';

export type Theme = 'system' | 'light' | 'dark';

// Custom event name for theme changes
export const THEME_CHANGE_EVENT = 'theme-change';

/**
 * Converts a theme value to the corresponding map style
 * @param theme - The current theme ('system', 'light', or 'dark')
 * @returns The appropriate map style for the theme
 */
export const getMapThemeFromCurrentTheme = (theme: Theme): string => {
  if (theme === 'dark') return MAP_TILE_STYLE_DARK;
  if (theme === 'light') return MAP_TILE_STYLE_LIGHT;

  // For system theme, use the system preference
  if (typeof window !== 'undefined') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? MAP_TILE_STYLE_DARK
      : MAP_TILE_STYLE_LIGHT;
  }

  return MAP_TILE_STYLE_LIGHT;
};

/**
 * Hook for managing map theme based on application theme
 * @returns The current map theme style
 */
export const useMapTheme = () => {
  // Initialize map theme based on current settings
  const [mapTheme, setMapTheme] = useState(() => {
    if (typeof window === 'undefined') return MAP_TILE_STYLE_LIGHT;

    // Check for explicit theme in DOM
    const dataTheme = document.documentElement.getAttribute('data-theme');
    if (dataTheme === 'dark') return MAP_TILE_STYLE_DARK;
    if (dataTheme === 'light') return MAP_TILE_STYLE_LIGHT;

    // Check for saved theme in localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') return MAP_TILE_STYLE_DARK;
    if (savedTheme === 'light') return MAP_TILE_STYLE_LIGHT;

    // Fall back to system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? MAP_TILE_STYLE_DARK
      : MAP_TILE_STYLE_LIGHT;
  });

  /**
   * Ensures map theme is consistent with application theme
   */
  const ensureThemeConsistency = useCallback(() => {
    if (typeof window === 'undefined') return;

    const dataTheme = document.documentElement.getAttribute('data-theme');
    const savedTheme = localStorage.getItem('theme');

    let newTheme;

    // Determine the correct theme based on priority:
    // 1. Explicit DOM attribute
    // 2. localStorage setting
    // 3. System preference
    if (dataTheme === 'dark') {
      newTheme = MAP_TILE_STYLE_DARK;
    } else if (dataTheme === 'light') {
      newTheme = MAP_TILE_STYLE_LIGHT;
    } else if (!dataTheme && savedTheme === 'dark') {
      newTheme = MAP_TILE_STYLE_DARK;
    } else if (!dataTheme && savedTheme === 'light') {
      newTheme = MAP_TILE_STYLE_LIGHT;
    } else {
      newTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? MAP_TILE_STYLE_DARK
        : MAP_TILE_STYLE_LIGHT;
    }

    // Only update if theme has changed
    if (mapTheme !== newTheme) {
      setMapTheme(newTheme);
    }
  }, [mapTheme]);

  // Set up listeners for various theme change events
  useEffect(() => {
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleSystemThemeChange = () => ensureThemeConsistency();
    mediaQuery.addEventListener('change', handleSystemThemeChange);

    // Watch for DOM attribute changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (
          mutation.type === 'attributes' &&
          mutation.attributeName === 'data-theme'
        ) {
          ensureThemeConsistency();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });

    // Listen for custom theme change events
    window.addEventListener(THEME_CHANGE_EVENT, handleSystemThemeChange);

    // Listen for localStorage changes (for multi-tab support)
    window.addEventListener('storage', (e) => {
      if (e.key === 'theme') {
        handleSystemThemeChange();
      }
    });

    // Initial check
    ensureThemeConsistency();

    // Clean up all listeners
    return () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange);
      observer.disconnect();
      window.removeEventListener(THEME_CHANGE_EVENT, handleSystemThemeChange);
      window.removeEventListener('storage', handleSystemThemeChange);
    };
  }, [ensureThemeConsistency]);

  return mapTheme;
};

/**
 * Main theme hook for the application
 * @returns Object with current theme and function to change theme
 */
export const useTheme = () => {
  // Initialize theme from localStorage or default to system
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'system';
    return (localStorage.getItem('theme') as Theme) || 'system';
  });

  /**
   * Set theme and dispatch event to notify other components
   */
  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);

    // Dispatch custom event for theme change
    const event = new CustomEvent(THEME_CHANGE_EVENT, { detail: { theme: newTheme } });
    window.dispatchEvent(event);
  }, []);

  // Apply theme changes to DOM and localStorage
  useEffect(() => {
    const root = window.document.documentElement;

    if (theme === 'system') {
      // For system theme, remove attribute and localStorage entry
      root.removeAttribute('data-theme');
      localStorage.removeItem('theme');
    } else {
      // For explicit themes, set attribute and save to localStorage
      root.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
    }
  }, [theme]);

  return {
    theme,
    setTheme,
  };
};