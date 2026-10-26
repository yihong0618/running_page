import { createPortal } from 'react-dom';

/** Floating control to show/hide the map after it has scrolled off-screen. */
export function MapDockFab({
  expanded,
  labelShow,
  labelHide,
  onToggle,
}: {
  expanded: boolean;
  labelShow: string;
  labelHide: string;
  onToggle: () => void;
}) {
  return createPortal(
    <button
      type="button"
      onClick={onToggle}
      style={{
        bottom: 'calc(0.75rem + env(safe-area-inset-bottom, 0px))',
      }}
      className="fixed right-4 z-[70] flex cursor-pointer items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-card)] px-3.5 py-2.5 text-sm font-medium text-[var(--color-text)] shadow-lg transition-transform hover:scale-[1.03]"
      aria-pressed={expanded}
      title={expanded ? labelHide : labelShow}
      aria-label={expanded ? labelHide : labelShow}
    >
      <svg
        className="size-4 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
        />
      </svg>
      {expanded ? labelHide : labelShow}
    </button>,
    document.body
  );
}
