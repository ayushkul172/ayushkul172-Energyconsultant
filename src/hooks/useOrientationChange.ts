import { useEffect, useRef, useState } from 'react';

/**
 * Hook that listens for device orientation changes and triggers
 * a layout recalculation within 300ms. Uses a leading-edge debounce:
 * the first event fires immediately (within one frame), and subsequent
 * events within the 300ms window are coalesced.
 *
 * Requirements: 10.5
 */
export function useOrientationChange(): number {
  // A counter that increments on each orientation change to force re-renders
  const [orientationKey, setOrientationKey] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastTriggerRef = useRef<number>(0);

  useEffect(() => {
    const handleOrientationChange = () => {
      const now = Date.now();
      const timeSinceLast = now - lastTriggerRef.current;

      // Leading-edge: trigger immediately if 300ms has passed since last trigger
      if (timeSinceLast >= 300) {
        lastTriggerRef.current = now;
        setOrientationKey((prev) => prev + 1);
      } else {
        // Trailing-edge: coalesce rapid events, fire at end of 300ms window
        if (debounceRef.current !== null) {
          clearTimeout(debounceRef.current);
        }

        const remaining = 300 - timeSinceLast;
        debounceRef.current = setTimeout(() => {
          lastTriggerRef.current = Date.now();
          setOrientationKey((prev) => prev + 1);
          debounceRef.current = null;
        }, remaining);
      }
    };

    // Listen for the orientationchange event
    window.addEventListener('orientationchange', handleOrientationChange);

    // Also listen for resize as a fallback (some browsers fire resize instead)
    // but only trigger on actual orientation-like changes (width/height swap)
    let lastWidth = window.innerWidth;
    let lastHeight = window.innerHeight;

    const handleResize = () => {
      const newWidth = window.innerWidth;
      const newHeight = window.innerHeight;

      // Detect orientation change via dimension swap
      const wasLandscape = lastWidth > lastHeight;
      const isLandscape = newWidth > newHeight;

      if (wasLandscape !== isLandscape) {
        handleOrientationChange();
      }

      lastWidth = newWidth;
      lastHeight = newHeight;
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange);
      window.removeEventListener('resize', handleResize);
      if (debounceRef.current !== null) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return orientationKey;
}
