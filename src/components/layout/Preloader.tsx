import { useEffect, useRef, useState, useCallback } from 'react';
import gsap from 'gsap';
import { useReducedMotion } from '@/hooks/useReducedMotion';

export interface PreloaderProps {
  onComplete: () => void;
  minDuration?: number; // default 1500ms
  maxDuration?: number; // default 5000ms
}

/**
 * Computes the clamped preloader display time:
 * max(minDuration, min(loadDuration, maxDuration))
 */
export function clampDuration(
  loadDuration: number,
  minDuration: number = 1500,
  maxDuration: number = 5000
): number {
  return Math.max(minDuration, Math.min(loadDuration, maxDuration));
}

/**
 * Branded preloader component with AK logo animation, progress indicator,
 * and duration clamping (min 1500ms, max 5000ms).
 *
 * - Shows within 500ms of navigation start
 * - Tracks actual asset loading via document.readyState / window load event
 * - Fires onComplete callback when done, triggering hero cinematic sequence
 * - Respects prefers-reduced-motion
 */
export function Preloader({
  onComplete,
  minDuration = 1500,
  maxDuration = 5000,
}: PreloaderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLDivElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<gsap.core.Timeline | null>(null);

  const [progress, setProgress] = useState(0);
  const reducedMotion = useReducedMotion();
  const hasCompletedRef = useRef(false);
  const startTimeRef = useRef(Date.now());

  const handleComplete = useCallback(() => {
    if (hasCompletedRef.current) return;
    hasCompletedRef.current = true;

    const container = containerRef.current;
    if (!container) {
      onComplete();
      return;
    }

    // Fade out the preloader
    gsap.to(container, {
      opacity: 0,
      duration: reducedMotion ? 0.2 : 0.4,
      ease: 'power2.inOut',
      onComplete: () => {
        onComplete();
      },
    });
  }, [onComplete, reducedMotion]);

  // Track actual asset loading progress
  useEffect(() => {
    startTimeRef.current = Date.now();
    let loadResolved = false;
    let minTimerDone = false;
    let maxTimerFired = false;

    const tryComplete = () => {
      if (loadResolved && minTimerDone && !maxTimerFired) {
        handleComplete();
      }
    };

    // Min duration timer
    const minTimer = setTimeout(() => {
      minTimerDone = true;
      tryComplete();
    }, minDuration);

    // Max duration timer (safety cap)
    const maxTimer = setTimeout(() => {
      maxTimerFired = true;
      handleComplete();
    }, maxDuration);

    // Track loading progress
    const updateProgress = () => {
      if (document.readyState === 'complete') {
        setProgress(100);
        loadResolved = true;
        tryComplete();
      } else if (document.readyState === 'interactive') {
        setProgress(70);
      } else {
        setProgress(30);
      }
    };

    // Initial check
    updateProgress();

    // Listen for load events
    const onReadyStateChange = () => updateProgress();
    const onWindowLoad = () => {
      setProgress(100);
      loadResolved = true;
      tryComplete();
    };

    document.addEventListener('readystatechange', onReadyStateChange);
    window.addEventListener('load', onWindowLoad);

    // If already fully loaded
    if (document.readyState === 'complete') {
      setProgress(100);
      loadResolved = true;
      // Still respect minDuration
    }

    return () => {
      clearTimeout(minTimer);
      clearTimeout(maxTimer);
      document.removeEventListener('readystatechange', onReadyStateChange);
      window.removeEventListener('load', onWindowLoad);
    };
  }, [minDuration, maxDuration, handleComplete]);

  // GSAP logo animation
  useEffect(() => {
    if (reducedMotion) return;

    const logo = logoRef.current;
    const progressBar = progressBarRef.current;
    if (!logo || !progressBar) return;

    const tl = gsap.timeline({ repeat: -1, yoyo: true });
    timelineRef.current = tl;

    // Pulsing/scaling animation for the logo
    tl.fromTo(
      logo,
      { scale: 0.95, opacity: 0.8 },
      { scale: 1.05, opacity: 1, duration: 0.8, ease: 'power1.inOut' }
    );

    // Initial entrance animation
    gsap.fromTo(
      logo,
      { scale: 0, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.5, ease: 'back.out(1.7)' }
    );

    gsap.fromTo(
      progressBar,
      { opacity: 0, y: 10 },
      { opacity: 1, y: 0, duration: 0.3, delay: 0.3, ease: 'power2.out' }
    );

    return () => {
      tl.kill();
      timelineRef.current = null;
    };
  }, [reducedMotion]);

  // Animate progress bar width
  useEffect(() => {
    if (progressBarRef.current) {
      gsap.to(progressBarRef.current.querySelector('.preloader-fill'), {
        width: `${progress}%`,
        duration: 0.4,
        ease: 'power2.out',
      });
    }
  }, [progress]);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-[9999] flex flex-col items-center justify-center"
      style={{ backgroundColor: 'var(--color-background, #0f172a)' }}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Loading portfolio"
    >
      {/* AK Logo */}
      <div
        ref={logoRef}
        className="flex items-center justify-center mb-8"
        aria-hidden="true"
      >
        <div className="relative w-24 h-24 flex items-center justify-center">
          {/* Outer ring glow */}
          {!reducedMotion && (
            <div
              className="absolute inset-0 rounded-full"
              style={{
                background:
                  'radial-gradient(circle, rgba(6, 182, 212, 0.3) 0%, transparent 70%)',
                animation: reducedMotion ? 'none' : undefined,
              }}
            />
          )}
          {/* Logo text */}
          <span
            className="text-5xl font-montserrat font-bold tracking-tight select-none"
            style={{ color: 'var(--color-accent, #06b6d4)' }}
          >
            AK
          </span>
        </div>
      </div>

      {/* Progress indicator */}
      <div
        ref={progressBarRef}
        className="w-48 h-1 rounded-full overflow-hidden"
        style={{ backgroundColor: 'rgba(6, 182, 212, 0.15)' }}
      >
        <div
          className="preloader-fill h-full rounded-full"
          style={{
            backgroundColor: 'var(--color-accent, #06b6d4)',
            width: '0%',
            transition: reducedMotion ? 'width 0.2s ease' : undefined,
          }}
        />
      </div>

      {/* Loading text */}
      <p
        className="mt-4 text-sm font-roboto"
        style={{ color: 'var(--color-text-muted, #64748b)' }}
      >
        Loading...
      </p>
    </div>
  );
}

export default Preloader;
