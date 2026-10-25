import { useSyncExternalStore } from 'react';

export type PlaybackPrefs = {
  showEndpoints: boolean;
  showStats: boolean;
};

const STORAGE_KEY = 'playback-prefs';

const DEFAULTS: PlaybackPrefs = {
  showEndpoints: true,
  showStats: true,
};

let current: PlaybackPrefs | null = null;
const listeners = new Set<() => void>();

function read(): PlaybackPrefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULTS };
    const parsed = JSON.parse(raw) as Partial<PlaybackPrefs>;
    return {
      showEndpoints: parsed.showEndpoints !== false,
      showStats: parsed.showStats !== false,
    };
  } catch {
    return { ...DEFAULTS };
  }
}

function ensure(): PlaybackPrefs {
  if (!current) current = read();
  return current;
}

export function getPlaybackPrefs(): PlaybackPrefs {
  return ensure();
}

export function setPlaybackPrefs(patch: Partial<PlaybackPrefs>): void {
  current = { ...ensure(), ...patch };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
  } catch {
    /* private mode */
  }
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function usePlaybackPrefs(): PlaybackPrefs {
  return useSyncExternalStore(subscribe, getPlaybackPrefs, () => DEFAULTS);
}
