import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

/**
 * Scroll animation types supported by the controller.
 */
export type ScrollAnimationType =
  | 'fadeInUp'
  | 'staggerChildren'
  | 'tiltIn'
  | 'splitText'
  | 'parallax';

/**
 * Configuration for registering a scroll-triggered animation.
 */
export interface ScrollAnimationConfig {
  trigger: HTMLElement;
  animation: ScrollAnimationType;
  options?: {
    staggerDelay?: number;   // default 100ms
    threshold?: number;      // default 0.2
    parallaxSpeed?: number;  // 0.3–0.7
  };
}

/** Maximum number of staggered children per section */
const MAX_STAGGER_ITEMS = 10;

/** Default IntersectionObserver threshold */
const DEFAULT_THRESHOLD = 0.2;

/** Track all active ScrollTrigger instances for cleanup */
const activeTriggers: ScrollTrigger[] = [];

/** Track all active IntersectionObservers for cleanup */
const activeObservers: IntersectionObserver[] = [];

/**
 * Applies the final animated state to an element (no animation played).
 * Used for elements already visible on page load.
 */
function applyFinalState(element: HTMLElement, animation: ScrollAnimationType): void {
  switch (animation) {
    case 'fadeInUp':
      gsap.set(element, { opacity: 1, y: 0 });
      break;
    case 'staggerChildren': {
      const children = Array.from(element.children).slice(0, MAX_STAGGER_ITEMS);
      children.forEach((child) => {
        gsap.set(child, { opacity: 1, y: 0 });
      });
      break;
    }
    case 'tiltIn':
      gsap.set(element, { opacity: 1, rotateX: 0 });
      break;
    case 'splitText':
      gsap.set(element, { opacity: 1 });
      // Individual words should already be visible
      const words = element.querySelectorAll('[data-split-word]');
      words.forEach((word) => {
        gsap.set(word, { opacity: 1, y: 0 });
      });
      break;
    case 'parallax':
      // Parallax elements don't need a "final state" — they just stay in place
      break;
  }
}

/**
 * Sets the initial hidden state for an element before animation.
 */
function setInitialState(element: HTMLElement, animation: ScrollAnimationType): void {
  switch (animation) {
    case 'fadeInUp':
      gsap.set(element, { opacity: 0, y: 40 });
      break;
    case 'staggerChildren': {
      const children = Array.from(element.children).slice(0, MAX_STAGGER_ITEMS);
      children.forEach((child) => {
        gsap.set(child, { opacity: 0, y: 30 });
      });
      break;
    }
    case 'tiltIn':
      gsap.set(element, { opacity: 0, rotateX: -15 });
      break;
    case 'splitText':
      gsap.set(element, { opacity: 1 });
      const words = element.querySelectorAll('[data-split-word]');
      words.forEach((word) => {
        gsap.set(word, { opacity: 0, y: 20 });
      });
      break;
    case 'parallax':
      // No initial state needed for parallax
      break;
  }
}

/**
 * Plays the entrance animation for an element.
 */
function playAnimation(
  element: HTMLElement,
  animation: ScrollAnimationType,
  staggerDelay: number
): void {
  switch (animation) {
    case 'fadeInUp':
      gsap.to(element, {
        opacity: 1,
        y: 0,
        duration: 0.6,
        ease: 'power2.out',
      });
      break;
    case 'staggerChildren': {
      const children = Array.from(element.children).slice(0, MAX_STAGGER_ITEMS);
      gsap.to(children, {
        opacity: 1,
        y: 0,
        duration: 0.5,
        ease: 'power2.out',
        stagger: staggerDelay,
      });
      break;
    }
    case 'tiltIn':
      gsap.to(element, {
        opacity: 1,
        rotateX: 0,
        duration: 0.6,
        ease: 'power2.out',
      });
      break;
    case 'splitText': {
      const words = element.querySelectorAll('[data-split-word]');
      gsap.to(Array.from(words), {
        opacity: 1,
        y: 0,
        duration: 0.06,
        ease: 'power1.out',
        stagger: 0.06,
      });
      break;
    }
    case 'parallax':
      // Parallax is handled separately via registerParallax
      break;
  }
}

/**
 * Registers a scroll-triggered animation for an element.
 *
 * Uses IntersectionObserver with configurable threshold (default 0.2).
 * Animations are one-shot: once triggered, they don't reverse on scroll-up.
 */
export function registerScrollAnimation(config: ScrollAnimationConfig): void {
  const { trigger, animation, options } = config;
  const threshold = options?.threshold ?? DEFAULT_THRESHOLD;
  const staggerDelay = (options?.staggerDelay ?? 100) / 1000; // Convert ms to seconds

  // For parallax, delegate to registerParallax
  if (animation === 'parallax') {
    const speed = options?.parallaxSpeed ?? 0.5;
    registerParallax(trigger, speed);
    return;
  }

  // Set initial hidden state
  setInitialState(trigger, animation);

  // Use IntersectionObserver for one-shot trigger
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          playAnimation(trigger, animation, staggerDelay);
          // One-shot: disconnect after triggering
          observer.unobserve(trigger);
        }
      });
    },
    { threshold }
  );

  observer.observe(trigger);
  activeObservers.push(observer);
}

/**
 * Registers a parallax effect on an element.
 *
 * The element moves at a fraction of the scroll speed (0.3–0.7x),
 * creating a depth illusion.
 */
export function registerParallax(element: HTMLElement, speed: number): void {
  // Clamp speed to valid range
  const clampedSpeed = Math.max(0.3, Math.min(0.7, speed));

  const trigger = ScrollTrigger.create({
    trigger: element,
    start: 'top bottom',
    end: 'bottom top',
    scrub: true,
    onUpdate: (self) => {
      const displacement = self.progress * 100 * (1 - clampedSpeed);
      gsap.set(element, { y: -displacement });
    },
  });

  activeTriggers.push(trigger);
}

/**
 * Checks which elements are already visible in the viewport on page load
 * and applies their final animated state immediately (skipping entrance animation).
 *
 * Should be called once after initial DOM render.
 */
export function checkInitialVisibility(
  elements: HTMLElement[],
  configs?: Map<HTMLElement, { animation: ScrollAnimationType }>
): void {
  elements.forEach((element) => {
    const rect = element.getBoundingClientRect();
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

    // Element is considered visible if at least 20% is in viewport
    const visibleRatio = Math.min(
      Math.max(0, Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0)),
      rect.height
    ) / rect.height;

    if (visibleRatio >= DEFAULT_THRESHOLD) {
      // Look up the animation type from the configs map, or default to fadeInUp
      const config = configs?.get(element);
      const animation = config?.animation ?? 'fadeInUp';
      applyFinalState(element, animation);

      // Mark as already animated so registerScrollAnimation won't re-animate
      element.setAttribute('data-scroll-animated', 'true');
    }
  });
}

/**
 * Kills all registered ScrollTrigger instances and disconnects all
 * IntersectionObservers. Call on component unmount or page navigation.
 */
export function killAllScrollTriggers(): void {
  // Kill GSAP ScrollTrigger instances
  activeTriggers.forEach((trigger) => {
    trigger.kill();
  });
  activeTriggers.length = 0;

  // Disconnect IntersectionObservers
  activeObservers.forEach((observer) => {
    observer.disconnect();
  });
  activeObservers.length = 0;
}
