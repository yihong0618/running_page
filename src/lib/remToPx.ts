export function remToPx(remValue: string): number {
  const rootFontSize =
    typeof window === 'undefined'
      ? 16
      : parseFloat(window.getComputedStyle(document.documentElement).fontSize);

  return parseFloat(remValue) * rootFontSize;
}
