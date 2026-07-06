import { useRef, useState, useCallback, useEffect } from 'react';
import gsap from 'gsap';

export type NavigationDirection = 'forward' | 'reverse';

export interface UsePageTurnerOptions {
  /** Total number of pages */
  totalPages: number;
  /** Initial page index (0-based) */
  initialPage?: number;
  /** Whether to use performance fallback (crossfade) */
  shouldFallback?: boolean;
  /** Whether on mobile (use slide instead of 3D flip) */
  isMobile?: boolean;
  /** Callback when page changes */
  onPageChange?: (page: number) => void;
}

export interface UsePageTurnerReturn {
  currentPage: number;
  isAnimating: boolean;
  goToPage: (targetPage: number) => void;
  goNext: () => void;
  goPrev: () => void;
  /** Refs to attach to each page wrapper div */
  pageRefs: React.MutableRefObject<(HTMLDivElement | null)[]>;
}

/**
 * Computes the navigation direction for a page transition.
 * Returns 'forward' when target > current, 'reverse' when target < current.
 */
export function getNavigationDirection(
  current: number,
  target: number
): NavigationDirection {
  return target > current ? 'forward' : 'reverse';
}

/**
 * Hook encapsulating GSAP page-turn logic with 3D flip transitions.
 *
 * - Forward flip: current page Y 0°→-90°, next page Y 90°→0° (800ms, power2.inOut)
 * - Reverse flip: current page Y 0°→90°, previous page Y -90°→0° (800ms, power2.inOut)
 * - Performance fallback: crossfade (opacity 0→1, 400ms)
 * - Mobile: horizontal slide + fade instead of 3D flip
 * - isAnimating flag discards navigation inputs during animation
 */
export function usePageTurner({
  totalPages,
  initialPage = 0,
  shouldFallback = false,
  isMobile = false,
  onPageChange,
}: UsePageTurnerOptions): UsePageTurnerReturn {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [isAnimating, setIsAnimating] = useState(false);
  const pageRefs = useRef<(HTMLDivElement | null)[]>([]);
  const timelineRef = useRef<gsap.core.Timeline | null>(null);

  // Keep refs array sized correctly
  useEffect(() => {
    pageRefs.current = pageRefs.current.slice(0, totalPages);
  }, [totalPages]);

  const animateFlip3D = useCallback(
    (fromIndex: number, toIndex: number, direction: NavigationDirection) => {
      const fromPage = pageRefs.current[fromIndex];
      const toPage = pageRefs.current[toIndex];
      if (!fromPage || !toPage) return;

      const tl = gsap.timeline({
        onComplete: () => {
          setIsAnimating(false);
          timelineRef.current = null;
        },
      });
      timelineRef.current = tl;

      // Set initial states
      gsap.set(toPage, {
        display: 'block',
        opacity: 1,
        rotateY: direction === 'forward' ? 90 : -90,
      });

      // Animate current page out
      tl.to(
        fromPage,
        {
          rotateY: direction === 'forward' ? -90 : 90,
          duration: 0.8,
          ease: 'power2.inOut',
        },
        0
      );

      // Animate next page in
      tl.to(
        toPage,
        {
          rotateY: 0,
          duration: 0.8,
          ease: 'power2.inOut',
        },
        0
      );

      // Hide the from page when done
      tl.set(fromPage, { display: 'none', rotateY: 0 });
    },
    []
  );

  const animateCrossfade = useCallback(
    (fromIndex: number, toIndex: number) => {
      const fromPage = pageRefs.current[fromIndex];
      const toPage = pageRefs.current[toIndex];
      if (!fromPage || !toPage) return;

      const tl = gsap.timeline({
        onComplete: () => {
          setIsAnimating(false);
          timelineRef.current = null;
        },
      });
      timelineRef.current = tl;

      // Show the target page behind current
      gsap.set(toPage, { display: 'block', opacity: 0 });

      // Crossfade
      tl.to(fromPage, { opacity: 0, duration: 0.4, ease: 'power2.inOut' }, 0);
      tl.to(toPage, { opacity: 1, duration: 0.4, ease: 'power2.inOut' }, 0);

      // Hide from page when done
      tl.set(fromPage, { display: 'none', opacity: 1 });
    },
    []
  );

  const animateMobileSlide = useCallback(
    (fromIndex: number, toIndex: number, direction: NavigationDirection) => {
      const fromPage = pageRefs.current[fromIndex];
      const toPage = pageRefs.current[toIndex];
      if (!fromPage || !toPage) return;

      const tl = gsap.timeline({
        onComplete: () => {
          setIsAnimating(false);
          timelineRef.current = null;
        },
      });
      timelineRef.current = tl;

      const slideDistance = direction === 'forward' ? '-100%' : '100%';
      const slideFrom = direction === 'forward' ? '100%' : '-100%';

      // Set initial state for incoming page
      gsap.set(toPage, {
        display: 'block',
        opacity: 0,
        x: slideFrom,
      });

      // Slide out current page + fade
      tl.to(
        fromPage,
        {
          x: slideDistance,
          opacity: 0,
          duration: 0.8,
          ease: 'power2.inOut',
        },
        0
      );

      // Slide in next page + fade
      tl.to(
        toPage,
        {
          x: '0%',
          opacity: 1,
          duration: 0.8,
          ease: 'power2.inOut',
        },
        0
      );

      // Reset from page
      tl.set(fromPage, { display: 'none', x: '0%', opacity: 1 });
    },
    []
  );

  const goToPage = useCallback(
    (targetPage: number) => {
      // Discard input if animating
      if (isAnimating) return;

      // Validate bounds
      if (targetPage < 0 || targetPage >= totalPages) return;

      // No-op if already on target page
      if (targetPage === currentPage) return;

      setIsAnimating(true);
      const direction = getNavigationDirection(currentPage, targetPage);

      // Choose animation based on conditions
      if (shouldFallback) {
        animateCrossfade(currentPage, targetPage);
      } else if (isMobile) {
        animateMobileSlide(currentPage, targetPage, direction);
      } else {
        animateFlip3D(currentPage, targetPage, direction);
      }

      setCurrentPage(targetPage);
      onPageChange?.(targetPage);
    },
    [
      isAnimating,
      totalPages,
      currentPage,
      shouldFallback,
      isMobile,
      animateCrossfade,
      animateMobileSlide,
      animateFlip3D,
      onPageChange,
    ]
  );

  const goNext = useCallback(() => {
    if (currentPage < totalPages - 1) {
      goToPage(currentPage + 1);
    }
  }, [currentPage, totalPages, goToPage]);

  const goPrev = useCallback(() => {
    if (currentPage > 0) {
      goToPage(currentPage - 1);
    }
  }, [currentPage, goToPage]);

  // Clean up timeline on unmount
  useEffect(() => {
    return () => {
      timelineRef.current?.kill();
    };
  }, []);

  return {
    currentPage,
    isAnimating,
    goToPage,
    goNext,
    goPrev,
    pageRefs,
  };
}
