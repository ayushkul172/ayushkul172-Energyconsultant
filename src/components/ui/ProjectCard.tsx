import { useRef, useEffect, useCallback, useState } from 'react';
import gsap from 'gsap';
import type { SpotlightProject } from '@/types';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { cn } from '@/utils/cn';

export interface ProjectCardProps {
  project: SpotlightProject;
  onExpand: (project: SpotlightProject, originRect: DOMRect) => void;
  index: number;
}

/**
 * ProjectCard — innovative interactive card with:
 * - 3D tilt on hover (max 12° rotation following cursor)
 * - Animated spotlight/cursor glow that follows mouse
 * - Floating tech stack pills that animate on hover
 * - Animated impact counter (0 → target, 1.5s ease-out)
 * - Glass morphism design with gradient accent border
 * - Image parallax on hover
 */
export function ProjectCard({ project, onExpand, index }: ProjectCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const countersRef = useRef<HTMLSpanElement[]>([]);
  const hasEnteredViewport = useRef(false);
  const hasCounterAnimated = useRef(false);
  const prefersReducedMotion = useReducedMotion();
  const [isHovered, setIsHovered] = useState(false);

  // ─── Scroll-triggered entrance ─────────────────────────────────────────────
  useEffect(() => {
    const card = cardRef.current;
    if (!card || hasEnteredViewport.current) return;

    if (prefersReducedMotion) {
      gsap.set(card, { opacity: 1, y: 0 });
      hasEnteredViewport.current = true;
      return;
    }

    gsap.set(card, { opacity: 0, y: 60, scale: 0.95 });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasEnteredViewport.current) {
            hasEnteredViewport.current = true;
            gsap.to(card, {
              opacity: 1,
              y: 0,
              scale: 1,
              duration: 0.8,
              delay: index * 0.15,
              ease: 'power3.out',
            });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.15 }
    );

    observer.observe(card);
    return () => observer.disconnect();
  }, [prefersReducedMotion, index]);

  // ─── Counter animation ─────────────────────────────────────────────────────
  useEffect(() => {
    const card = cardRef.current;
    if (!card || hasCounterAnimated.current) return;

    if (prefersReducedMotion) {
      countersRef.current.forEach((el, i) => {
        if (el) el.textContent = project.results[i]?.metric ?? '';
      });
      hasCounterAnimated.current = true;
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasCounterAnimated.current) {
            hasCounterAnimated.current = true;
            animateCounters();
            observer.disconnect();
          }
        });
      },
      { threshold: 0.2 }
    );

    observer.observe(card);
    return () => observer.disconnect();
  }, [prefersReducedMotion, project.results]);

  const animateCounters = useCallback(() => {
    project.results.forEach((result, i) => {
      const el = countersRef.current[i];
      if (!el) return;

      const numericMatch = result.metric.match(/(\d+)/);
      if (!numericMatch) {
        el.textContent = result.metric;
        return;
      }

      const target = parseInt(numericMatch[1], 10);
      const suffix = result.metric.replace(numericMatch[1], '');
      const obj = { value: 0 };

      gsap.to(obj, {
        value: target,
        duration: 1.5,
        delay: 0.3,
        ease: 'power2.out',
        onUpdate: () => { el.textContent = `${Math.round(obj.value)}${suffix}`; },
        onComplete: () => { el.textContent = result.metric; },
      });
    });
  }, [project.results]);

  // ─── Mouse tracking for 3D tilt + spotlight glow ───────────────────────────
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (prefersReducedMotion) return;
      const card = cardRef.current;
      const glow = glowRef.current;
      const img = imageRef.current;
      if (!card) return;

      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const offsetX = (x - centerX) / centerX;
      const offsetY = (y - centerY) / centerY;

      // 3D tilt (max 12°)
      gsap.to(card, {
        rotateY: offsetX * 12,
        rotateX: -offsetY * 12,
        transformPerspective: 1000,
        duration: 0.4,
        ease: 'power2.out',
      });

      // Spotlight glow follows cursor
      if (glow) {
        glow.style.background = `radial-gradient(circle 250px at ${x}px ${y}px, ${getGlowFromAccent(project.accentColor).color}, transparent 70%)`;
      }

      // Image parallax
      if (img) {
        gsap.to(img, {
          x: offsetX * 8,
          y: offsetY * 5,
          scale: 1.08,
          duration: 0.4,
          ease: 'power2.out',
        });
      }
    },
    [prefersReducedMotion, project.accentColor]
  );

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    if (prefersReducedMotion) return;
    const card = cardRef.current;
    const img = imageRef.current;
    if (card) {
      gsap.to(card, { rotateX: 0, rotateY: 0, duration: 0.5, ease: 'power2.out' });
    }
    if (img) {
      gsap.to(img, { x: 0, y: 0, scale: 1, duration: 0.5, ease: 'power2.out' });
    }
  }, [prefersReducedMotion]);

  const handleClick = useCallback(() => {
    const card = cardRef.current;
    if (!card) return;
    onExpand(project, card.getBoundingClientRect());
  }, [project, onExpand]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleClick();
      }
    },
    [handleClick]
  );

  return (
    <div
      ref={cardRef}
      className={cn(
        'project-card group relative rounded-2xl overflow-hidden cursor-pointer',
        'bg-[var(--color-card-surface)]/80 backdrop-blur-sm',
        'border border-white/[0.08]',
        'transition-all duration-500',
        'hover:border-white/20 hover:shadow-2xl',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]'
      )}
      style={{ willChange: 'transform', transformStyle: 'preserve-3d' }}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`View details for ${project.title}`}
      data-project-card
      data-index={index}
    >
      {/* Animated spotlight glow that follows cursor */}
      <div
        ref={glowRef}
        className={cn(
          'absolute inset-0 rounded-2xl pointer-events-none transition-opacity duration-300',
          isHovered ? 'opacity-60' : 'opacity-0'
        )}
        aria-hidden="true"
      />

      {/* Top accent gradient line */}
      <div
        className={cn(
          'absolute top-0 left-0 right-0 h-[2px]',
          'bg-gradient-to-r opacity-60 group-hover:opacity-100 transition-opacity duration-300',
          project.accentColor
        )}
        aria-hidden="true"
      />

      {/* Project Image with parallax */}
      <div className="relative h-44 sm:h-52 overflow-hidden">
        <img
          ref={imageRef}
          src={project.image}
          alt={project.title}
          className="w-full h-full object-cover"
          loading="lazy"
        />
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-card-surface)] via-[var(--color-card-surface)]/30 to-transparent" />

        {/* Floating "Click to explore" indicator */}
        <div className={cn(
          'absolute bottom-3 right-3 px-3 py-1.5 rounded-full text-xs font-medium',
          'bg-white/10 backdrop-blur-md border border-white/20 text-white/90',
          'transition-all duration-300 translate-y-2 opacity-0',
          'group-hover:translate-y-0 group-hover:opacity-100'
        )}>
          <span className="flex items-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            Explore
          </span>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-5 sm:p-6">
        {/* Title */}
        <h3 className="text-lg sm:text-xl font-heading font-bold text-[var(--color-text)] mb-3 group-hover:text-[var(--color-accent)] transition-colors duration-300">
          {project.title}
        </h3>

        {/* Tech Stack — animated pills */}
        <div className="flex flex-wrap gap-2 mb-5">
          {project.techStack.map((tech, i) => (
            <span
              key={tech}
              className={cn(
                'text-xs px-2.5 py-1 rounded-full font-medium',
                'bg-white/5 text-[var(--color-text-subtle)] border border-white/10',
                'transition-all duration-300',
                'group-hover:border-[var(--color-accent)]/30 group-hover:text-[var(--color-accent)] group-hover:bg-[var(--color-accent)]/5'
              )}
              style={{
                transitionDelay: isHovered ? `${i * 50}ms` : '0ms',
              }}
            >
              {tech}
            </span>
          ))}
        </div>

        {/* Impact Metrics — with glowing counters */}
        <div className="grid grid-cols-3 gap-3 pt-4 border-t border-white/[0.06]">
          {project.results.map((result, i) => (
            <div key={i} className="text-center group/metric">
              <span
                ref={(el) => { if (el) countersRef.current[i] = el; }}
                className={cn(
                  'block text-xl sm:text-2xl font-bold mb-0.5',
                  'bg-gradient-to-r bg-clip-text text-transparent',
                  project.accentColor,
                  'group-hover/metric:drop-shadow-[0_0_8px_rgba(6,182,212,0.5)]'
                )}
              >
                {prefersReducedMotion ? result.metric : '0'}
              </span>
              <span className="text-[10px] sm:text-xs text-[var(--color-text-muted)] line-clamp-2 leading-tight">
                {result.description}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom accent glow on hover */}
      <div
        className={cn(
          'absolute bottom-0 left-1/4 right-1/4 h-[1px] transition-all duration-500',
          'bg-gradient-to-r',
          project.accentColor,
          isHovered ? 'opacity-80 blur-[2px] h-[3px]' : 'opacity-0'
        )}
        aria-hidden="true"
      />
    </div>
  );
}

// ─── Utility ─────────────────────────────────────────────────────────────────

function getGlowFromAccent(accentColor: string): { color: string; colorFaint: string } {
  const colorMap: Record<string, { color: string; colorFaint: string }> = {
    'from-cyan-500': { color: 'rgba(6, 182, 212, 0.35)', colorFaint: 'rgba(6, 182, 212, 0.12)' },
    'from-purple-500': { color: 'rgba(168, 85, 247, 0.35)', colorFaint: 'rgba(168, 85, 247, 0.12)' },
    'from-green-500': { color: 'rgba(34, 197, 94, 0.35)', colorFaint: 'rgba(34, 197, 94, 0.12)' },
    'from-orange-500': { color: 'rgba(249, 115, 22, 0.35)', colorFaint: 'rgba(249, 115, 22, 0.12)' },
  };

  const fromClass = accentColor.split(' ').find((cls) => cls.startsWith('from-'));
  if (fromClass && colorMap[fromClass]) return colorMap[fromClass];
  return { color: 'rgba(6, 182, 212, 0.35)', colorFaint: 'rgba(6, 182, 212, 0.12)' };
}

export default ProjectCard;
