import { useRef, useCallback } from 'react';

export type SwipeDirection = 'left' | 'right';

export interface UseSwipeGestureOptions {
  /** Callback fired when a valid horizontal swipe is detected */
  onSwipe?: (direction: SwipeDirection) => void;
  /** Callback fired when a valid left swipe (finger moves left) is detected */
  onSwipeLeft?: () => void;
  /** Callback fired when a valid right swipe (finger moves right) is detected */
  onSwipeRight?: () => void;
  /** Minimum horizontal distance in pixels to recognize a swipe (default: 50) */
  minDistance?: number;
}

export interface SwipeHandlers {
  onTouchStart: (e: React.TouchEvent) => void;
  onTouchMove: (e: React.TouchEvent) => void;
  onTouchEnd: (e: React.TouchEvent) => void;
}

/**
 * Detects horizontal swipe gestures on touch-enabled devices.
 *
 * - Tracks touchstart coordinates
 * - On touchmove: if horizontal movement > vertical and > 10px, calls preventDefault
 *   to block vertical scroll during the swipe gesture
 * - On touchend: if |deltaX| >= minDistance (default 50px) and predominantly horizontal,
 *   fires onSwipe callback with direction ('left' | 'right')
 *
 * Returns event handlers to spread on a container element.
 *
 * @example
 * ```tsx
 * const handlers = useSwipeGesture({
 *   onSwipe: (direction) => {
 *     if (direction === 'left') goNext();
 *     else goPrev();
 *   },
 * });
 *
 * return <div {...handlers}>...</div>;
 * ```
 */
export function useSwipeGesture(options: UseSwipeGestureOptions): SwipeHandlers {
  const { onSwipe, onSwipeLeft, onSwipeRight, minDistance = 50 } = options;
  const touchStartRef = useRef<{ x: number; y: number } | null>(null);

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0];
    touchStartRef.current = { x: touch.clientX, y: touch.clientY };
  }, []);

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    if (!touchStartRef.current) return;

    const touch = e.touches[0];
    const deltaX = Math.abs(touch.clientX - touchStartRef.current.x);
    const deltaY = Math.abs(touch.clientY - touchStartRef.current.y);

    // Prevent vertical scrolling during a predominantly horizontal swipe gesture
    if (deltaX > deltaY && deltaX > 10) {
      e.preventDefault();
    }
  }, []);

  const onTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!touchStartRef.current) return;

      const touch = e.changedTouches[0];
      const deltaX = touch.clientX - touchStartRef.current.x;
      const deltaY = touch.clientY - touchStartRef.current.y;

      // Recognize horizontal swipes: |deltaX| >= minDistance and predominantly horizontal
      if (Math.abs(deltaX) >= minDistance && Math.abs(deltaX) > Math.abs(deltaY)) {
        const direction: SwipeDirection = deltaX < 0 ? 'left' : 'right';
        onSwipe?.(direction);
        if (direction === 'left') onSwipeLeft?.();
        if (direction === 'right') onSwipeRight?.();
      }

      touchStartRef.current = null;
    },
    [onSwipe, onSwipeLeft, onSwipeRight, minDistance]
  );

  return { onTouchStart, onTouchMove, onTouchEnd };
}
