export interface SmoothScrollOptions {
  /** Offset in pixels to account for fixed navbar height. Defaults to 0. */
  offset?: number;
  /** Scroll behavior. Defaults to 'smooth'. */
  behavior?: ScrollBehavior;
  /** Block alignment. Defaults to 'start'. */
  block?: ScrollLogicalPosition;
}

/**
 * Smoothly scrolls the page to an element identified by its ID.
 * Supports an offset option to account for fixed headers/navbars.
 *
 * @param elementId - The ID of the target element (without the # prefix)
 * @param options - Scroll configuration options
 */
export function smoothScrollTo(
  elementId: string,
  options: SmoothScrollOptions = {}
): void {
  const { offset = 0, behavior = 'smooth', block = 'start' } = options;

  const element = document.getElementById(elementId);
  if (!element) return;

  if (offset === 0) {
    element.scrollIntoView({ behavior, block });
  } else {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.scrollY - offset;

    window.scrollTo({
      top: offsetPosition,
      behavior,
    });
  }
}
