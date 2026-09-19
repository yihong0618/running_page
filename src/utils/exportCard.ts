/** Capture the full card, and restore live layout even if rendering fails. */
export async function exportCard(element: HTMLElement, filename: string) {
  const { toPng } = await import('html-to-image');
  const previous = {
    overflow: element.style.overflow,
    width: element.style.width,
    maxWidth: element.style.maxWidth,
    scrollLeft: element.scrollLeft,
  };
  const computed = getComputedStyle(element);
  const width = Math.ceil(
    Math.max(
      element.getBoundingClientRect().width,
      element.scrollWidth + parseFloat(computed.paddingRight) + 2
    )
  );
  element.classList.add('exporting');
  element.style.overflow = 'visible';
  element.style.maxWidth = 'none';
  element.style.width = `${width}px`;
  try {
    await document.fonts.ready;
    await new Promise(requestAnimationFrame);
    const bounds = element.getBoundingClientRect();
    const dataUrl = await toPng(element, {
      backgroundColor: computed.backgroundColor,
      width: Math.ceil(bounds.width),
      height: Math.ceil(bounds.height),
      pixelRatio: 2,
      filter: (node) =>
        !(
          node instanceof HTMLElement && node.hasAttribute('data-export-hidden')
        ),
    });
    const link = document.createElement('a');
    link.download = filename;
    link.href = dataUrl;
    link.click();
    return dataUrl;
  } finally {
    element.classList.remove('exporting');
    element.style.overflow = previous.overflow;
    element.style.width = previous.width;
    element.style.maxWidth = previous.maxWidth;
    element.scrollLeft = previous.scrollLeft;
  }
}
