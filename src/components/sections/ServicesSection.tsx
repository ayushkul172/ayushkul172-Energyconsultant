import { useRef, useCallback } from 'react';
import gsap from 'gsap';
import { services } from '@/data/services';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { useScrollAnimation } from '@/hooks/useScrollAnimation';
import { useSplitTextReveal } from '@/hooks/useSplitTextReveal';
import { cn } from '@/utils/cn';

/**
 * ServicesSection — displays service cards in a responsive grid
 * with animated gradient borders (glow-pulse 2s cycle),
 * staggered scroll-triggered reveal (100ms delays),
 * and hover effects with accent color glow.
 *
 * Uses useScrollAnimation hook for staggered children entrance.
 *
 * Requirements: 2.1, 11.4
 */
function ServicesSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const prefersReducedMotion = useReducedMotion();

  // Split-text reveal for section heading
  const headingRef = useRef<HTMLHeadingElement>(null);
  const { isRevealed: _headingRevealed } = useSplitTextReveal(headingRef);

  // Use useScrollAnimation for staggered children reveal (Requirement 2.1)
  const { ref: gridRef } = useScrollAnimation({
    type: 'staggerChildren',
    options: {
      staggerDelay: 0.1, // 100ms between items
      threshold: 0.2,
      maxStaggerItems: 10,
    },
  });

  // Scroll animation for subtitle paragraph
  const { ref: subtitleRef } = useScrollAnimation({
    type: 'fadeInUp',
    options: { threshold: 0.2, duration: 0.6 },
  });

  return (
    <section
      ref={sectionRef}
      id="services"
      className="min-h-screen py-20 px-4 sm:px-6 lg:px-8 overflow-hidden"
      style={{ backgroundColor: 'var(--color-background)' }}
    >
      {/* Section Heading */}
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl md:text-4xl lg:text-5xl font-heading font-bold text-center mb-4 text-[var(--color-text)]" ref={headingRef}>
          What I Offer
        </h2>
        <p ref={subtitleRef as unknown as React.RefObject<HTMLParagraphElement>} className="text-center text-[var(--color-text-subtle)] mb-12 max-w-2xl mx-auto">
          Professional services spanning AI development, web engineering, energy consulting, and data science.
        </p>

        {/* Responsive Service Cards Grid */}
        <div
          ref={gridRef as unknown as React.RefObject<HTMLDivElement>}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
        >
          {services.map((service) => (
            <ServiceCard
              key={service.title}
              service={service}
              prefersReducedMotion={prefersReducedMotion}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── ServiceCard Component ─────────────────────────────────────────────────────

interface ServiceCardProps {
  service: (typeof services)[number];
  prefersReducedMotion: boolean;
}

function ServiceCard({ service, prefersReducedMotion }: ServiceCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);

  // Handle hover glow effect
  const handleMouseEnter = useCallback(() => {
    if (prefersReducedMotion || !cardRef.current) return;

    gsap.to(cardRef.current, {
      scale: 1.03,
      duration: 0.3,
      ease: 'power2.out',
    });
  }, [prefersReducedMotion]);

  const handleMouseLeave = useCallback(() => {
    if (prefersReducedMotion || !cardRef.current) return;

    gsap.to(cardRef.current, {
      scale: 1,
      duration: 0.3,
      ease: 'power2.out',
    });
  }, [prefersReducedMotion]);

  // Extract gradient colors for hover glow from accentColor (e.g., "from-blue-600 to-cyan-500")
  const glowStyle = getGlowStyle(service.accentColor);

  return (
    <div
      ref={cardRef}
      className={cn(
        'gradient-border',
        'group relative rounded-xl p-6',
        'transition-shadow duration-300 ease-out',
        'cursor-default'
      )}
      style={{
        backgroundColor: '#1e293b',
        ...(!prefersReducedMotion ? {} : { opacity: 1 }),
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Hover glow overlay */}
      <div
        className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        style={{
          boxShadow: `0 0 30px ${glowStyle.color}, 0 0 60px ${glowStyle.colorFaint}`,
        }}
      />

      {/* Icon */}
      <div
        className={cn(
          'w-12 h-12 rounded-lg flex items-center justify-center mb-4',
          'bg-gradient-to-br',
          service.accentColor || 'from-cyan-500 to-blue-600'
        )}
      >
        <i className={cn(service.icon, 'text-xl text-white')} aria-hidden="true" />
      </div>

      {/* Title */}
      <h3 className="text-lg font-heading font-semibold text-[var(--color-text)] mb-2">
        {service.title}
      </h3>

      {/* Description */}
      <p className="text-sm text-[var(--color-text-subtle)] mb-4 leading-relaxed">
        {service.description}
      </p>

      {/* Pricing Tag */}
      <span
        className={cn(
          'inline-block px-3 py-1 rounded-full text-xs font-medium',
          'bg-[var(--color-accent)]/10 text-[var(--color-accent)]',
          'border border-[var(--color-accent)]/20'
        )}
      >
        {service.pricing}
      </span>
    </div>
  );
}

// ─── Utility: Extract glow color from Tailwind gradient class ──────────────────

function getGlowStyle(accentColor?: string): { color: string; colorFaint: string } {
  // Map Tailwind gradient classes to rgba colors for box-shadow glow
  const colorMap: Record<string, string> = {
    'from-blue-600': 'rgba(37, 99, 235, 0.4)',
    'from-purple-600': 'rgba(147, 51, 234, 0.4)',
    'from-green-600': 'rgba(22, 163, 74, 0.4)',
    'from-orange-600': 'rgba(234, 88, 12, 0.4)',
    'from-indigo-600': 'rgba(79, 70, 229, 0.4)',
    'from-pink-600': 'rgba(219, 39, 119, 0.4)',
    'from-amber-500': 'rgba(245, 158, 11, 0.4)',
    'from-emerald-500': 'rgba(16, 185, 129, 0.4)',
  };

  const faintMap: Record<string, string> = {
    'from-blue-600': 'rgba(37, 99, 235, 0.15)',
    'from-purple-600': 'rgba(147, 51, 234, 0.15)',
    'from-green-600': 'rgba(22, 163, 74, 0.15)',
    'from-orange-600': 'rgba(234, 88, 12, 0.15)',
    'from-indigo-600': 'rgba(79, 70, 229, 0.15)',
    'from-pink-600': 'rgba(219, 39, 119, 0.15)',
    'from-amber-500': 'rgba(245, 158, 11, 0.15)',
    'from-emerald-500': 'rgba(16, 185, 129, 0.15)',
  };

  if (!accentColor) {
    return { color: 'rgba(6, 182, 212, 0.4)', colorFaint: 'rgba(6, 182, 212, 0.15)' };
  }

  // Extract the "from-*" part from the accentColor string
  const fromClass = accentColor.split(' ').find((cls) => cls.startsWith('from-'));

  return {
    color: (fromClass && colorMap[fromClass]) || 'rgba(6, 182, 212, 0.4)',
    colorFaint: (fromClass && faintMap[fromClass]) || 'rgba(6, 182, 212, 0.15)',
  };
}

export default ServicesSection;
