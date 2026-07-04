/**
 * HeroSection Component
 *
 * Cinematic reveal sequence triggered after preloader completes:
 * 1. Background fade in (600ms)
 * 2. Typewriter name animation (50ms/char)
 * 3. Subtitle slide-up (400ms)
 * 4. CTA scale-in (300ms)
 *
 * Features:
 * - Rotating title animation cycling roles every 3s with 500ms crossfade
 * - Canvas particle background (50+ particles on desktop, 20 on mobile)
 * - Mouse attraction within 150px at 2px/frame
 * - Profile image with gradient border
 * - Reduced motion: static dots, no movement, simplified reveals
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 10.3
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import gsap from 'gsap';
import { useParticles } from '@/hooks/useParticles';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { smoothScrollTo } from '@/utils/smoothScroll';

// ─── Constants ────────────────────────────────────────────────────────────────

const HERO_NAME = 'Ayush Kulshrestha';
const ROTATING_TITLES = ['Energy Data Analyst', 'AI Consultant', 'Automation Expert'];
const PROFILE_IMAGE_URL =
  'https://raw.githubusercontent.com/ayushkul172/Energyconsultant/main/Ayushprofile.png';

const TITLE_CYCLE_INTERVAL = 3000; // 3 seconds
const CROSSFADE_DURATION = 500; // 500ms

interface HeroSectionProps {
  /** Whether the hero reveal sequence should play (true after preloader completes) */
  isRevealed?: boolean;
  /** Callback to navigate to a section by index */
  onNavigate?: (pageIndex: number) => void;
}

export default function HeroSection({ isRevealed = true, onNavigate }: HeroSectionProps) {
  const reducedMotion = useReducedMotion();

  // ─── Refs ────────────────────────────────────────────────────────────────
  const sectionRef = useRef<HTMLElement>(null);
  const nameRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const bgRef = useRef<HTMLDivElement>(null);

  // ─── State ───────────────────────────────────────────────────────────────
  const [currentTitleIndex, setCurrentTitleIndex] = useState(0);
  const [titleVisible, setTitleVisible] = useState(true);
  const [hasRevealed, setHasRevealed] = useState(false);

  // ─── Particle System ─────────────────────────────────────────────────────
  const { canvasRef } = useParticles({ enabled: isRevealed, count: 50 });

  // ─── Rotating Title Animation ────────────────────────────────────────────
  useEffect(() => {
    if (!isRevealed) return;

    const interval = setInterval(() => {
      // Start crossfade out
      setTitleVisible(false);

      // After half the crossfade, change text and fade in
      setTimeout(() => {
        setCurrentTitleIndex((prev) => (prev + 1) % ROTATING_TITLES.length);
        setTitleVisible(true);
      }, CROSSFADE_DURATION / 2);
    }, TITLE_CYCLE_INTERVAL);

    return () => clearInterval(interval);
  }, [isRevealed]);

  // ─── Cinematic Reveal Sequence ───────────────────────────────────────────
  useEffect(() => {
    if (!isRevealed || hasRevealed) return;

    // Mark as revealed to prevent re-triggering
    setHasRevealed(true);

    if (reducedMotion) {
      // Reduced motion: just show everything immediately with opacity
      gsap.set([bgRef.current, nameRef.current, subtitleRef.current, ctaRef.current, profileRef.current], {
        opacity: 1,
      });
      if (nameRef.current) nameRef.current.textContent = HERO_NAME;
      return;
    }

    // Use requestAnimationFrame to ensure DOM is painted before animating
    requestAnimationFrame(() => {
    // Set initial states
    gsap.set(bgRef.current, { opacity: 0 });
    gsap.set(nameRef.current, { opacity: 0 });
    gsap.set(subtitleRef.current, { opacity: 0, y: 30 });
    gsap.set(ctaRef.current, { opacity: 0, scale: 0.8 });
    gsap.set(profileRef.current, { opacity: 0, scale: 0.9 });

    // Build the cinematic timeline
    const tl = gsap.timeline({ delay: 0.3 });

    // 1. Background fade in (600ms)
    tl.to(bgRef.current, {
      opacity: 1,
      duration: 0.6,
      ease: 'power2.out',
    });

    // 2. Profile image scale in
    tl.to(profileRef.current, {
      opacity: 1,
      scale: 1,
      duration: 0.5,
      ease: 'back.out(1.4)',
    }, '-=0.2');

    // 3. Typewriter name animation (50ms/char)
    tl.to(nameRef.current, {
      opacity: 1,
      duration: 0.1,
      onComplete: () => {
        typewriterEffect(nameRef.current, HERO_NAME);
      },
    });

    // Wait for typewriter to complete (50ms * characters + buffer)
    const typewriterDuration = (HERO_NAME.length * 50) / 1000;
    tl.to({}, { duration: typewriterDuration });

    // 4. Subtitle slide-up (400ms)
    tl.to(subtitleRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.4,
      ease: 'power2.out',
    });

    // 5. CTA buttons scale-in (300ms)
    tl.to(ctaRef.current, {
      opacity: 1,
      scale: 1,
      duration: 0.3,
      ease: 'back.out(1.7)',
    });
    }); // end requestAnimationFrame

    return () => {
      // Timeline cleanup handled by GSAP internally
    };
  }, [isRevealed, hasRevealed, reducedMotion]);

  // ─── Typewriter Effect ───────────────────────────────────────────────────
  const typewriterTimeouts = useRef<ReturnType<typeof setTimeout>[]>([]);
  
  const typewriterEffect = useCallback((element: HTMLElement | null, text: string) => {
    if (!element) return;

    // Clear any previous typewriter timeouts
    typewriterTimeouts.current.forEach(clearTimeout);
    typewriterTimeouts.current = [];
    
    element.textContent = '';

    for (let i = 0; i < text.length; i++) {
      const timeout = setTimeout(() => {
        element.textContent = text.substring(0, i + 1);
      }, i * 50); // 50ms per character
      typewriterTimeouts.current.push(timeout);
    }
  }, []);

  // ─── CTA Handlers ───────────────────────────────────────────────────────
  const handleViewProjects = useCallback(() => {
    if (onNavigate) {
      onNavigate(2); // Projects is at index 2
    } else {
      smoothScrollTo('projects', { offset: 80 });
    }
  }, [onNavigate]);

  const handleGetInTouch = useCallback(() => {
    if (onNavigate) {
      onNavigate(5); // Contact is at index 5
    } else {
      smoothScrollTo('contact', { offset: 80 });
    }
  }, [onNavigate]);

  // ─── Render ──────────────────────────────────────────────────────────────
  return (
    <section
      ref={sectionRef}
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
      aria-label="Hero section"
    >
      {/* Background layer */}
      <div
        ref={bgRef}
        className="absolute inset-0 bg-[var(--color-background)]"
      />

      {/* Particle Canvas — behind content */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-auto"
        style={{ zIndex: 1 }}
        aria-hidden="true"
      />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center text-center px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
        {/* Profile Image */}
        <div
          ref={profileRef}
          className="mb-6 sm:mb-8"
        >
          <div className="relative w-32 h-32 sm:w-40 sm:h-40 lg:w-48 lg:h-48 rounded-full p-[3px] bg-gradient-to-br from-[var(--color-accent)] via-[var(--color-accent-secondary)] to-[var(--color-accent)] overflow-hidden">
            <img
              src={PROFILE_IMAGE_URL}
              alt="Ayush Kulshrestha"
              className="w-full h-full rounded-full object-cover bg-[var(--color-card-surface)]"
              loading="eager"
              onError={(e) => {
                // Fallback: hide broken image and show initials
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
            {/* Fallback initials shown behind the image */}
            <div className="absolute inset-[3px] rounded-full bg-[var(--color-card-surface)] flex items-center justify-center -z-10">
              <span className="text-3xl font-heading font-bold text-[var(--color-accent)]">AK</span>
            </div>
          </div>
        </div>

        {/* Name with typewriter effect */}
        <h1
          ref={nameRef}
          className="text-3xl sm:text-4xl lg:text-6xl font-montserrat font-bold text-[var(--color-text)] mb-2"
          style={{ minHeight: '1.2em' }}
        >
          {reducedMotion ? HERO_NAME : ''}
        </h1>

        {/* Dashing animated intro — staggered sentence reveal with glow effects */}
        <div className="mb-6 max-w-3xl mx-auto text-center space-y-4">
          {/* Line 1 — Title with glowing border card */}
          <div className="animate-intro-s1 inline-block px-6 py-2 rounded-full border border-[var(--color-accent)]/40 bg-[var(--color-accent)]/5 glow-card">
            <p className="text-sm sm:text-base lg:text-lg font-body">
              <span className="text-[var(--color-accent)] font-bold text-glow">Upstream Energy &amp; AI Professional</span>
              <span className="text-[var(--color-text-subtle)]"> · </span>
              <span className="text-[var(--color-text)] font-bold counter-highlight">6+ years</span>
              <span className="text-[var(--color-text-subtle)]"> at </span>
              <span className="text-[var(--color-text)] font-semibold">Wood Mackenzie</span>
              <span className="text-[var(--color-text-subtle)]"> &amp; </span>
              <span className="text-[var(--color-text)] font-semibold">KPMG</span>
            </p>
          </div>

          {/* Line 2 — Subsea expertise with animated underline */}
          <p className="text-sm sm:text-base text-[var(--color-text-subtle)] font-body leading-relaxed animate-intro-s2">
            Combining deep <span className="text-[var(--color-accent)] font-semibold animated-underline">subsea production expertise</span> — Christmas Trees, SURF systems, FPSOs, manifolds, topsides, wellheads
          </p>

          {/* Line 3 — ML stats with glowing number badges */}
          <div className="animate-intro-s3 flex flex-wrap items-center justify-center gap-3 text-sm sm:text-base text-[var(--color-text-subtle)] font-body">
            <span>Built production-grade ML systems</span>
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/30 stat-badge">
              <span className="text-[var(--color-accent)] font-bold">PyTorch</span>
              <span className="text-[var(--color-text-muted)]">·</span>
              <span className="text-[var(--color-text)] font-bold">3.5M params</span>
              <span className="text-[var(--color-text-muted)]">·</span>
              <span className="text-[var(--color-accent)] font-bold">98%</span>
            </span>
          </div>

          {/* Line 4 — Python automation with big 90% */}
          <div className="animate-intro-s4 flex flex-wrap items-center justify-center gap-2 text-sm sm:text-base text-[var(--color-text-subtle)] font-body">
            <span className="text-[var(--color-accent)] font-semibold animated-underline">Python automation pipelines</span>
            <span>reducing manual processes by</span>
            <span className="text-2xl sm:text-3xl font-bold text-[var(--color-text)] counter-highlight pulse-number">90%</span>
          </div>

          {/* Line 5 — Lifecycle with arrow flow */}
          <div className="animate-intro-s5 overflow-hidden">
            <p className="text-xs sm:text-sm text-[var(--color-text-muted)] font-body">
              <span className="text-[var(--color-accent)] font-semibold">Subsea Contract Lifecycle:</span>
            </p>
            <div className="flex flex-wrap items-center justify-center gap-1 mt-1 text-xs sm:text-sm lifecycle-flow">
              <span className="px-2 py-0.5 rounded bg-[var(--color-accent)]/10 text-[var(--color-accent)] font-medium lifecycle-step">Concept</span>
              <span className="text-[var(--color-accent)]">→</span>
              <span className="px-2 py-0.5 rounded bg-[var(--color-accent)]/10 text-[var(--color-accent)] font-medium lifecycle-step">Pre-FEED</span>
              <span className="text-[var(--color-accent)]">→</span>
              <span className="px-2 py-0.5 rounded bg-[var(--color-accent)]/10 text-[var(--color-accent)] font-medium lifecycle-step">FEED</span>
              <span className="text-[var(--color-accent)]">→</span>
              <span className="px-2 py-0.5 rounded bg-[var(--color-accent)]/10 text-[var(--color-accent)] font-medium lifecycle-step">EPC</span>
              <span className="text-[var(--color-accent)]">→</span>
              <span className="px-2 py-0.5 rounded bg-[var(--color-accent)]/10 text-[var(--color-accent)] font-medium lifecycle-step">Installation</span>
              <span className="text-[var(--color-accent)]">→</span>
              <span className="px-2 py-0.5 rounded bg-[var(--color-accent)]/10 text-[var(--color-accent)] font-medium lifecycle-step">Hook-up &amp; Commissioning</span>
            </div>
          </div>
        </div>

        {/* Rotating Title */}
        <div
          ref={subtitleRef}
          className="mb-8 sm:mb-10"
        >
          <p
            className="text-lg sm:text-xl lg:text-2xl font-roboto text-[var(--color-accent)] transition-opacity"
            style={{
              opacity: titleVisible ? 1 : 0,
              transitionDuration: `${CROSSFADE_DURATION / 2}ms`,
            }}
            aria-live="polite"
            aria-atomic="true"
          >
            {ROTATING_TITLES[currentTitleIndex]}
          </p>
        </div>

        {/* CTA Buttons */}
        <div
          ref={ctaRef}
          className="flex flex-col sm:flex-row gap-4"
        >
          <button
            onClick={handleViewProjects}
            className="px-8 py-3 rounded-lg font-montserrat font-semibold text-sm sm:text-base
              bg-[var(--color-accent)] text-[var(--color-background)]
              hover:bg-[var(--color-accent-secondary)] hover:scale-105
              transition-all duration-300 ease-out
              focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:ring-offset-2 focus:ring-offset-[var(--color-background)]"
            aria-label="View Projects section"
          >
            View Projects
          </button>
          <button
            onClick={handleGetInTouch}
            className="px-8 py-3 rounded-lg font-montserrat font-semibold text-sm sm:text-base
              border-2 border-[var(--color-accent)] text-[var(--color-accent)]
              hover:bg-[var(--color-accent)] hover:text-[var(--color-background)] hover:scale-105
              transition-all duration-300 ease-out
              focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:ring-offset-2 focus:ring-offset-[var(--color-background)]"
            aria-label="Get in touch - scroll to contact section"
          >
            Get In Touch
          </button>
        </div>
      </div>
    </section>
  );
}
