import { useEffect, useRef, useState, type RefObject } from 'react';
import gsap from 'gsap';
import { useReducedMotion } from './useReducedMotion';

/**
 * Supported scroll animation types.
 */
export type ScrollAnimationType =
  | 'fadeInUp'
  | 'staggerChildren'
  | 'tiltIn'
  | 'parallax';

/**
 * Configuration options for the scroll animation.
 */
export interface ScrollAnimationOptions {
  /** IntersectionObserver threshold (default: 0.2) */
  threshold?: number;
  /** Animation duration in seconds (default: 0.6) */
  duration?: number;
  /** Translate-Y distance in pixels for fadeInUp (default: 40) */
  distance?: number;
  /** Delay before animation starts in seconds (default: 0) */
  delay?: number;
  /** Stagger delay between children in seconds (default: 0.1) */
  staggerDelay?: number;
  /** Parallax speed factor 0.3–0.7 (default: 0.5) */
  parallaxSpeed?: number;
  /** Maximum number of stagger children (default: 10) */
  maxStaggerItems?: number;
  /** GSAP easing string (default: 'power2.out') */
  ease?: string;
}

export interface ScrollAnimationConfig {
  type: ScrollAnimationType;
  options?: ScrollAnimationOptions;
}

export interface UseScrollAnimationReturn {
  /** Ref to attach to the target element */
  ref: RefObject<HTMLElement | null>;
  /** Whether the element is currently in view (triggered) */
  isInView: boolean;
}

/**
 * Generic hook that applies a scroll-triggered GSAP animation to a ref element.
 *
 * Uses IntersectionObserver with a configurable threshold (default 0.2).
 * Animations fire once and do not reverse on scroll-up (one-shot).
 * Elements already in viewport on load get their final state immediately.
 * Respects prefers-reduced-motion by falling back to a simple opacity fade (300ms).
 *
 * @param config - Animation type and options
 * @returns Object with ref and isInView state
 *
 * Requirements: 2.1, 2.5, 2.6, 2.7
 */
export function useScrollAnimation(
  config: ScrollAnimationConfig
): UseScrollAnimationReturn;

/**
 * Overload: accepts an existing ref and animation config.
 *
 * @param ref - React ref to the target element
 * @param config - Animation type and options
 * @returns Object with ref and isInView state
 */
export function useScrollAnimation(
  refOrConfig: RefObject<HTMLElement | null> | ScrollAnimationConfig,
  config?: ScrollAnimationConfig
): UseScrollAnimationReturn;

export function useScrollAnimation(
  refOrConfig: RefObject<HTMLElement | null> | ScrollAnimationConfig,
  maybeConfig?: ScrollAnimationConfig
): UseScrollAnimationReturn {
  // Determine whether the first argument is a ref or a config
  const isRefArg = refOrConfig !== null && 'current' in refOrConfig;
  const internalRef = useRef<HTMLElement | null>(null);
  const ref = isRefArg ? (refOrConfig as RefObject<HTMLElement | null>) : internalRef;
  const resolvedConfig = isRefArg ? maybeConfig! : (refOrConfig as ScrollAnimationConfig);

  const [isInView, setIsInView] = useState(false);
  const reducedMotion = useReducedMotion();
  const observerRef = useRef<IntersectionObserver | null>(null);
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    const element = ref.current;
    if (!element || hasTriggeredRef.current) return;

    const { type, options } = resolvedConfig;
    const threshold = options?.threshold ?? 0.2;
    const duration = options?.duration ?? 0.6;
    const distance = options?.distance ?? 40;
    const delay = options?.delay ?? 0;
    const staggerDelay = options?.staggerDelay ?? 0.1;
    const maxStaggerItems = options?.maxStaggerItems ?? 10;
    const ease = options?.ease ?? 'power2.out';

    // Check if element is already in viewport on load
    const rect = element.getBoundingClientRect();
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
    const visibleRatio = Math.min(
      Math.max(0, Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0)),
      rect.height
    ) / (rect.height || 1);

    if (visibleRatio >= threshold) {
      // Element is already in viewport — apply final state immediately
      hasTriggeredRef.current = true;
      setIsInView(true);
      applyFinalState(element, type, maxStaggerItems);
      return;
    }

    // Set initial hidden state (unless reduced motion — we still need initial state for the fade)
    if (!reducedMotion) {
      setInitialState(element, type, distance, maxStaggerItems);
    } else {
      gsap.set(element, { opacity: 0 });
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasTriggeredRef.current) {
            hasTriggeredRef.current = true;
            setIsInView(true);

            if (reducedMotion) {
              // Reduced motion fallback: simple opacity fade (300ms)
              gsap.to(element, { opacity: 1, duration: 0.3, ease: 'none' });
            } else {
              playAnimation(element, type, {
                duration,
                distance,
                delay,
                staggerDelay,
                maxStaggerItems,
                ease,
              });
            }

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
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reducedMotion]);

  return { ref, isInView };
}

/**
 * Applies the final animated state to an element immediately (no animation).
 * Used when elements are already visible in viewport on initial load.
 */
function applyFinalState(
  element: HTMLElement,
  type: ScrollAnimationType,
  maxStaggerItems: number
): void {
  switch (type) {
    case 'fadeInUp':
      gsap.set(element, { opacity: 1, y: 0 });
      break;
    case 'staggerChildren': {
      const children = Array.from(element.children).slice(0, maxStaggerItems);
      gsap.set(element, { opacity: 1 });
      children.forEach((child) => {
        gsap.set(child, { opacity: 1, y: 0 });
      });
      break;
    }
    case 'tiltIn':
      gsap.set(element, { opacity: 1, rotateX: 0 });
      break;
    case 'parallax':
      // Parallax elements don't need a "final state"
      break;
  }
}

/**
 * Sets the initial hidden state before animation plays.
 */
function setInitialState(
  element: HTMLElement,
  type: ScrollAnimationType,
  distance: number,
  maxStaggerItems: number
): void {
  switch (type) {
    case 'fadeInUp':
      gsap.set(element, { opacity: 0, y: distance });
      break;
    case 'staggerChildren': {
      const children = Array.from(element.children).slice(0, maxStaggerItems);
      children.forEach((child) => {
        gsap.set(child, { opacity: 0, y: distance * 0.75 });
      });
      break;
    }
    case 'tiltIn':
      gsap.set(element, { opacity: 0, rotateX: -15 });
      break;
    case 'parallax':
      // No initial state needed for parallax
      break;
  }
}

interface AnimationParams {
  duration: number;
  distance: number;
  delay: number;
  staggerDelay: number;
  maxStaggerItems: number;
  ease: string;
}

/**
 * Plays the entrance animation for the element.
 */
function playAnimation(
  element: HTMLElement,
  type: ScrollAnimationType,
  params: AnimationParams
): void {
  const { duration, delay, staggerDelay, maxStaggerItems, ease } = params;

  switch (type) {
    case 'fadeInUp':
      gsap.to(element, {
        opacity: 1,
        y: 0,
        duration,
        delay,
        ease,
      });
      break;
    case 'staggerChildren': {
      const children = Array.from(element.children).slice(0, maxStaggerItems);
      gsap.to(children, {
        opacity: 1,
        y: 0,
        duration: duration * 0.83,
        delay,
        ease,
        stagger: staggerDelay,
      });
      break;
    }
    case 'tiltIn':
      gsap.to(element, {
        opacity: 1,
        rotateX: 0,
        duration,
        delay,
        ease,
      });
      break;
    case 'parallax':
      // Parallax is continuous and handled differently (via ScrollTrigger in scrollController)
      break;
  }
}
