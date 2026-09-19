import { createContext, use, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import { messages, type Locale } from '../i18n';
import { DEFAULT_LOCALE } from '../config';

interface LocaleContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

const LocaleContext = createContext<LocaleContextValue>({
  locale: 'zh',
  setLocale: () => {},
  t: (key) => key,
});

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => {
    const stored = localStorage.getItem('locale');
    return (stored as Locale) || DEFAULT_LOCALE;
  });

  const updateLocale = useCallback((l: Locale) => {
    setLocale(l);
    localStorage.setItem('locale', l);
  }, []);

  const t = useCallback(
    (key: string) => {
      return messages[locale][key] || key;
    },
    [locale]
  );

  return (
    <LocaleContext value={{ locale, setLocale: updateLocale, t }}>
      {children}
    </LocaleContext>
  );
}

export function useLocale() {
  return use(LocaleContext);
}
