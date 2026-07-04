import React, { useEffect, useState, useCallback, Children } from 'react';
import { usePageTurner } from '@/hooks/usePageTurner';
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor';

/**
 * PageTurner component props.
 * Each child element represents a "page" that takes full viewport height.
 */
export interface PageTurnerProps {
  children: React.ReactNode[];
  currentPage: number;
  onPageChange: (page: number) => void;
}

const MOBILE_BREAKPOINT = 768;

/**
 * Detects whether the viewport is below the mobile breakpoint.
 */
function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < MOBILE_BREAKPOINT;
  });

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return isMobile;
}

/**
 * PageTurner — 3D page-flip container for section navigation.
 *
 * Wraps each child section in a perspective container with 3D transforms.
 * - Desktop: 3D Y-axis flip animation (800ms, power2.inOut)
 * - Mobile (<768px): horizontal slide + fade
 * - Performance fallback: crossfade (400ms) when shouldFallback is true
 * - Discards navigation inputs during animation via isAnimating flag
 *
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 10.2
 */
export function PageTurner({ children, currentPage, onPageChange }: PageTurnerProps) {
  const isMobile = useIsMobile();
  const { shouldFallback } = usePerformanceMonitor();
  const totalPages = Children.count(children);

  const { isAnimating, goToPage, pageRefs } = usePageTurner({
    totalPages,
    initialPage: currentPage,
    shouldFallback,
    isMobile,
    onPageChange,
  });

  // Sync external currentPage prop with internal state
  const handleExternalPageChange = useCallback(
    (page: number) => {
      if (!isAnimating) {
        goToPage(page);
      }
    },
    [isAnimating, goToPage]
  );

  // React to external currentPage prop changes
  useEffect(() => {
    handleExternalPageChange(currentPage);
  }, [currentPage, handleExternalPageChange]);

  const childArray = Children.toArray(children);

  return (
    <div
      className="relative w-full h-screen overflow-hidden"
      style={{
        perspective: '1200px',
      }}
      data-animating={isAnimating}
    >
      {childArray.map((child, index) => (
        <div
          key={index}
          ref={(el) => {
            pageRefs.current[index] = el;
          }}
          className="absolute inset-0 w-full h-screen overflow-y-auto overflow-x-hidden"
          style={{
            transformStyle: 'preserve-3d',
            backfaceVisibility: 'hidden',
            display: index === currentPage ? 'block' : 'none',
            willChange: 'transform, opacity',
          }}
          aria-hidden={index !== currentPage}
        >
          {child}
        </div>
      ))}
    </div>
  );
}

export default PageTurner;
