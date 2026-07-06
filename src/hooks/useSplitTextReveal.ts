import { useEffect, useRef, useState, type RefObject } from 'react';
import gsap from 'gsap';
import { useReducedMotion } from './useReducedMotion';

export interface UseSplitTextRevealOptions {
  /** Delay per word in milliseconds (default: 60) */
  delayPerWord?: number;
  /** Animation duration per word in seconds (default: 0.4) */
  duration?: number;
  /** Translate-Y distance in pixels (default: 20) */
  distance?: number;
  /** IntersectionObserver threshold (default: 0.2) */
  threshold?: number;
  /** GSAP easing (default: 'power2.out') */
  ease?: string;
}

export interface UseSplitTextRevealReturn {
  /** Ref to attach to the target element */
  ref: RefObject<HTMLElement | null>;
  /** Whether the reveal animation has completed */
  isRevealed: boolean;
}

/**
 * Hook that splits an element's text content into word-level spans and
 * animates each word with a staggered fade + translate-up effect on scroll.
 *
 * Each word at index `i` receives a delay of `i * delayPerWord` (default 60ms).
 * Words are wrapped in inline-block spans with a `data-split-word` attribute.
 *
 * Respects prefers-reduced-motion: shows text with an opacity fade (300ms)
 * instead of word-level animations.
 *
 * @param options - Configuration options for the animation
 * @returns Object with ref and isRevealed state
 *
 * Requirements: 2.2
 */
export function useSplitTextReveal(
  options?: UseSplitTextRevealOptions
): UseSplitTextRevealReturn;

/**
 * Overload: accepts an existing ref and options.
 *
 * @param ref - React ref to the element whose text will be split and animated
 * @param options - Configuration options for the animation
 * @returns Object with ref and isRevealed state
 */
export function useSplitTextReveal(
  refOrOptions?: RefObject<HTMLElement | null> | UseSplitTextRevealOptions,
  maybeOptions?: UseSplitTextRevealOptions
): UseSplitTextRevealReturn;

export function useSplitTextReveal(
  refOrOptions?: RefObject<HTMLElement | null> | UseSplitTextRevealOptions,
  maybeOptions?: UseSplitTextRevealOptions
): UseSplitTextRevealReturn {
  // Determine whether the first argument is a ref or options
  const isRefArg = refOrOptions !== null && refOrOptions !== undefined && 'current' in refOrOptions;
  const internalRef = useRef<HTMLElement | null>(null);
  const ref = isRefArg ? (refOrOptions as RefObject<HTMLElement | null>) : internalRef;
  const resolvedOptions = isRefArg ? maybeOptions : (refOrOptions as UseSplitTextRevealOptions | undefined);

  const [isRevealed, setIsRevealed] = useState(false);
  const reducedMotion = useReducedMotion();
  const observerRef = useRef<IntersectionObserver | null>(null);
  const originalTextRef = useRef<string>('');
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    const element = ref.current;
    if (!element || hasTriggeredRef.current) return;

    const delayPerWord = (resolvedOptions?.delayPerWord ?? 60) / 1000; // Convert ms to seconds
    const duration = resolvedOptions?.duration ?? 0.4;
    const distance = resolvedOptions?.distance ?? 20;
    const threshold = resolvedOptions?.threshold ?? 0.2;
    const ease = resolvedOptions?.ease ?? 'power2.out';

    // Store original text for cleanup
    originalTextRef.current = element.textContent ?? '';

    // If reduced motion, set up for opacity fade trigger
    if (reducedMotion) {
      element.style.opacity = '0';

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && !hasTriggeredRef.current) {
              hasTriggeredRef.current = true;
              setIsRevealed(true);
              // Reduced motion: simple opacity fade (300ms)
              gsap.to(element, { opacity: 1, duration: 0.3, ease: 'none' });
              observer.unobserve(element);
            }
          });
        },
        { threshold }
      );

      // Check if already in viewport
      const rect = element.getBoundingClientRect();
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
      const visibleRatio = Math.min(
        Math.max(0, Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0)),
        rect.height
      ) / (rect.height || 1);

      if (visibleRatio >= threshold) {
        hasTriggeredRef.current = true;
        setIsRevealed(true);
        element.style.opacity = '1';
        return;
      }

      observer.observe(element);
      observerRef.current = observer;

      return () => {
        observer.disconnect();
      };
    }

    // Set element to visible container (words start hidden individually)
    element.style.opacity = '1';

    // Split text into word spans
    const text = element.textContent ?? '';
    const words = text.split(/\s+/).filter((w) => w.length > 0);

    if (words.length === 0) {
      setIsRevealed(true);
      return;
    }

    // Clear element and create word spans
    element.innerHTML = '';

    const wordSpans: HTMLSpanElement[] = words.map((word, index) => {
      const span = document.createElement('span');
      span.textContent = word;
      span.setAttribute('data-split-word', '');
      span.style.display = 'inline-block';
      span.style.opacity = '0';
      span.style.transform = `translateY(${distance}px)`;

      // Add space between words (except after last word)
      if (index < words.length - 1) {
        span.style.marginRight = '0.25em';
      }

      element.appendChild(span);
      return span;
    });

    // Check if element is already in viewport on load
    const rect = element.getBoundingClientRect();
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
    const visibleRatio = Math.min(
      Math.max(0, Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0)),
      rect.height
    ) / (rect.height || 1);

    if (visibleRatio >= threshold) {
      // Already in viewport: apply final state immediately
      hasTriggeredRef.current = true;
      setIsRevealed(true);
      wordSpans.forEach((span) => {
        span.style.opacity = '1';
        span.style.transform = 'translateY(0)';
      });
      return;
    }

    // Set up intersection observer for scroll trigger
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasTriggeredRef.current) {
            hasTriggeredRef.current = true;
            setIsRevealed(true);

            // Animate each word with staggered delay: i * 60ms
            wordSpans.forEach((span, i) => {
              gsap.to(span, {
                opacity: 1,
                y: 0,
                duration,
                delay: i * delayPerWord,
                ease,
              });
            });

            // One-shot: disconnect after triggering
            observer.unobserve(element);
          }
        });
      },
      { threshold }
    );

    observer.observe(element);
    observerRef.current = observer;

    return () => {
      observer.disconnect();
      // Restore original text on cleanup
      if (ref.current && originalTextRef.current) {
        ref.current.textContent = originalTextRef.current;
        ref.current.style.opacity = '';
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reducedMotion]);

  return { ref, isRevealed };
}
