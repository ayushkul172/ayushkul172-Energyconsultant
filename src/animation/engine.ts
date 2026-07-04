import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Flip } from 'gsap/Flip';

// ─── Plugin Registration ───────────────────────────────────────────────────────

/**
 * Registers GSAP plugins (ScrollTrigger, Flip).
 * Call once at app initialization.
 */
export function registerPlugins(): void {
  gsap.registerPlugin(ScrollTrigger, Flip);
}

// ─── Timeline Factory ──────────────────────────────────────────────────────────

export interface TimelineOptions {
  defaults?: gsap.TweenVars;
  paused?: boolean;
  onComplete?: () => void;
}

/**
 * Factory for creating GSAP timelines with optional defaults.
 */
export function createTimeline(options?: TimelineOptions): gsap.core.Timeline {
  return gsap.timeline({
    defaults: options?.defaults,
    paused: options?.paused ?? false,
    onComplete: options?.onComplete,
  });
}

// ─── Default Easing ────────────────────────────────────────────────────────────

const DEFAULT_EASING = 'power2.out';
const PAGE_TURN_EASING = 'power2.inOut';

// ─── Reduced Motion Fallback ───────────────────────────────────────────────────

function applyReducedMotionFallback(
  element: gsap.TweenTarget,
  duration: number = 0.3
): gsap.core.Tween {
  return gsap.fromTo(
    element,
    { opacity: 0 },
    { opacity: 1, duration, ease: 'none' }
  );
}

// ─── Animation Presets ─────────────────────────────────────────────────────────

export interface FadeInUpOptions {
  duration?: number;
  distance?: number;
  delay?: number;
  ease?: string;
  reducedMotion?: boolean;
}

/**
 * Fade + translate-up animation.
 * With reduced motion: simple opacity fade ≤300ms.
 */
export function fadeInUp(
  element: gsap.TweenTarget,
  options?: FadeInUpOptions
): gsap.core.Tween {
  if (options?.reducedMotion) {
    return applyReducedMotionFallback(element, 0.3);
  }

  const duration = options?.duration ?? 0.6;
  const distance = options?.distance ?? 40;
  const delay = options?.delay ?? 0;
  const ease = options?.ease ?? DEFAULT_EASING;

  return gsap.from(element, {
    opacity: 0,
    y: distance,
    duration,
    delay,
    ease,
  });
}

export interface StaggerChildrenOptions {
  staggerDelay?: number;
  duration?: number;
  distance?: number;
  ease?: string;
  reducedMotion?: boolean;
}

/**
 * Staggered fade-in for child elements of a parent container.
 * With reduced motion: simple opacity fade ≤300ms per child.
 */
export function staggerChildren(
  parent: Element,
  childSelector: string,
  options?: StaggerChildrenOptions
): gsap.core.Tween {
  const children = parent.querySelectorAll(childSelector);

  if (options?.reducedMotion) {
    return gsap.fromTo(
      children,
      { opacity: 0 },
      { opacity: 1, duration: 0.3, stagger: 0.05, ease: 'none' }
    );
  }

  const staggerDelay = options?.staggerDelay ?? 0.1;
  const duration = options?.duration ?? 0.5;
  const distance = options?.distance ?? 30;
  const ease = options?.ease ?? DEFAULT_EASING;

  return gsap.from(children, {
    opacity: 0,
    y: distance,
    duration,
    stagger: staggerDelay,
    ease,
  });
}

export interface TiltInOptions {
  duration?: number;
  startAngle?: number;
  delay?: number;
  ease?: string;
  reducedMotion?: boolean;
}

/**
 * 3D tilt-in animation: rotates from -15deg on X-axis to 0.
 * With reduced motion: simple opacity fade ≤300ms.
 */
export function tiltIn(
  element: gsap.TweenTarget,
  options?: TiltInOptions
): gsap.core.Tween {
  if (options?.reducedMotion) {
    return applyReducedMotionFallback(element, 0.3);
  }

  const duration = options?.duration ?? 0.6;
  const startAngle = options?.startAngle ?? -15;
  const delay = options?.delay ?? 0;
  const ease = options?.ease ?? DEFAULT_EASING;

  return gsap.from(element, {
    opacity: 0,
    rotateX: startAngle,
    transformPerspective: 1200,
    duration,
    delay,
    ease,
  });
}

export interface SplitTextRevealOptions {
  delayPerWord?: number;
  duration?: number;
  distance?: number;
  ease?: string;
  reducedMotion?: boolean;
}

/**
 * Word-level split text animation: splits text by whitespace,
 * wraps each word in a span, and animates with staggered fade + translate-up.
 * Each word at index i gets delay of i * delayPerWord (default 60ms).
 * With reduced motion: simple opacity fade ≤300ms.
 */
export function splitTextReveal(
  element: HTMLElement,
  options?: SplitTextRevealOptions
): gsap.core.Timeline {
  const tl = gsap.timeline();

  if (options?.reducedMotion) {
    tl.fromTo(element, { opacity: 0 }, { opacity: 1, duration: 0.3, ease: 'none' });
    return tl;
  }

  const delayPerWord = options?.delayPerWord ?? 0.06;
  const duration = options?.duration ?? 0.4;
  const distance = options?.distance ?? 20;
  const ease = options?.ease ?? DEFAULT_EASING;

  // Get the text content and split into words
  const text = element.textContent ?? '';
  const words = text.split(/\s+/).filter((w) => w.length > 0);

  // Clear element and create word spans
  element.textContent = '';
  element.style.display = 'inline';

  const wordSpans: HTMLSpanElement[] = words.map((word, index) => {
    const span = document.createElement('span');
    span.textContent = word;
    span.style.display = 'inline-block';
    span.style.opacity = '0';

    // Add space between words (except after last word)
    if (index < words.length - 1) {
      span.style.marginRight = '0.25em';
    }

    element.appendChild(span);
    return span;
  });

  // Animate each word with staggered delay
  tl.from(wordSpans, {
    opacity: 0,
    y: distance,
    duration,
    stagger: delayPerWord,
    ease,
  });

  return tl;
}

export interface ParallaxOptions {
  reducedMotion?: boolean;
}

/**
 * Parallax movement tied to scroll position.
 * Speed factor should be between 0.3 and 0.7 for subtle parallax.
 * With reduced motion: no parallax applied, returns a no-op tween.
 */
export function parallax(
  element: gsap.TweenTarget,
  speed: number,
  scrollTriggerConfig: ScrollTrigger.Vars,
  options?: ParallaxOptions
): gsap.core.Tween {
  if (options?.reducedMotion) {
    // No parallax for reduced motion — just ensure element is visible
    return gsap.set(element, { opacity: 1 }) as unknown as gsap.core.Tween;
  }

  // Clamp speed to valid range
  const clampedSpeed = Math.max(0.3, Math.min(0.7, speed));

  return gsap.to(element, {
    y: () => {
      const scrollDistance =
        ScrollTrigger.maxScroll(window) -
        (scrollTriggerConfig.start
          ? parseFloat(String(scrollTriggerConfig.start))
          : 0);
      return scrollDistance * clampedSpeed * -1;
    },
    ease: 'none',
    scrollTrigger: {
      trigger: element as gsap.DOMTarget,
      start: 'top bottom',
      end: 'bottom top',
      scrub: true,
      ...scrollTriggerConfig,
    },
  });
}

// ─── Exported Constants ────────────────────────────────────────────────────────

export { DEFAULT_EASING, PAGE_TURN_EASING };
