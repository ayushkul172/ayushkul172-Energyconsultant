import { useRef, useState, useEffect, useCallback } from 'react';
import gsap from 'gsap';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { useScrollAnimation } from '@/hooks/useScrollAnimation';
import { useSplitTextReveal } from '@/hooks/useSplitTextReveal';
import { cn } from '@/utils/cn';
import { skillCategories } from '@/data/skills';
import SkillBar from '@/components/ui/SkillBar';

/**
 * SkillsSection — displays skill categories (Programming, Analytics, AI/ML, Energy Domain)
 * with animated progress bars.
 *
 * - Categories revealed sequentially with 200ms stagger between groups.
 * - Each skill bar animates from 0 → proficiency% over 1.5s ease-out.
 * - Uses IntersectionObserver for visibility detection.
 * - Pauses animations on viewport exit, resumes on re-enter.
 * - Reduced motion: shows bars at final state immediately.
 *
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
 */
export default function SkillsSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const categoryRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [isInView, setIsInView] = useState(false);
  const [revealedCategories, setRevealedCategories] = useState<Set<number>>(new Set());
  const staggerTimerRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const reducedMotion = useReducedMotion();

  // Split-text reveal for section heading
  const headingRef = useRef<HTMLHeadingElement>(null);
  const { isRevealed: _headingRevealed } = useSplitTextReveal(headingRef);

  // Scroll animation for subtitle paragraph (Requirement 2.1)
  const { ref: subtitleRef } = useScrollAnimation({
    type: 'fadeInUp',
    options: { threshold: 0.2, duration: 0.6 },
  });

  // ─── IntersectionObserver for viewport detection ───────────────────────────
  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          setIsInView(entry.isIntersecting);
        });
      },
      { threshold: 0.2 }
    );

    observer.observe(section);

    return () => {
      observer.disconnect();
    };
  }, []);

  // ─── Sequential category reveal with 200ms stagger ─────────────────────────
  const revealCategories = useCallback(() => {
    if (reducedMotion) {
      // Reduced motion: reveal all immediately
      const allIndices = new Set(skillCategories.map((_, i) => i));
      setRevealedCategories(allIndices);
      return;
    }

    // Stagger reveal each category with 200ms delay between groups
    skillCategories.forEach((_, index) => {
      const timer = setTimeout(() => {
        setRevealedCategories((prev) => {
          const next = new Set(prev);
          next.add(index);
          return next;
        });
      }, index * 200);
      staggerTimerRef.current.push(timer);
    });
  }, [reducedMotion]);

  // ─── Trigger reveal when section comes into view ───────────────────────────
  useEffect(() => {
    if (isInView && revealedCategories.size === 0) {
      revealCategories();
    }
  }, [isInView, revealedCategories.size, revealCategories]);

  // ─── GSAP fade-in for category cards ───────────────────────────────────────
  useEffect(() => {
    if (reducedMotion) return;

    categoryRefs.current.forEach((ref, index) => {
      if (ref && revealedCategories.has(index)) {
        gsap.fromTo(
          ref,
          { opacity: 0, y: 20 },
          {
            opacity: 1,
            y: 0,
            duration: 0.5,
            ease: 'power2.out',
          }
        );
      }
    });
  }, [revealedCategories, reducedMotion]);

  // ─── Cleanup timers on unmount ─────────────────────────────────────────────
  useEffect(() => {
    return () => {
      staggerTimerRef.current.forEach(clearTimeout);
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      id="skills"
      className="min-h-screen py-20 px-4 md:px-8 lg:px-16 flex flex-col items-center justify-center overflow-hidden"
      aria-labelledby="skills-heading"
    >
      {/* Section Header */}
      <div className="w-full max-w-6xl mb-12 text-center">
        <h2
          id="skills-heading"
          ref={headingRef}
          className="text-3xl md:text-4xl lg:text-5xl font-heading text-[var(--color-text)] mb-4"
        >
          Technical Skills
        </h2>
        <p ref={subtitleRef as unknown as React.RefObject<HTMLParagraphElement>} className="text-[var(--color-text-subtle)] font-body text-base md:text-lg max-w-2xl mx-auto">
          A comprehensive overview of my technical proficiencies across programming, analytics, AI/ML, and energy domain expertise.
        </p>
      </div>

      {/* Skill Categories Grid */}
      <div className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
        {skillCategories.map((category, categoryIndex) => {
          const isRevealed = revealedCategories.has(categoryIndex);

          return (
            <div
              key={category.name}
              ref={(el) => { categoryRefs.current[categoryIndex] = el; }}
              className={cn(
                'rounded-xl p-5 md:p-6 border border-[var(--color-border)]',
                'bg-[var(--color-card-surface)]',
                'transition-opacity duration-300',
                !isRevealed && !reducedMotion && 'opacity-0'
              )}
              role="group"
              aria-label={`${category.name} skills`}
            >
              {/* Category Header */}
              <h3 className="text-lg md:text-xl font-heading text-[var(--color-accent)] mb-4 flex items-center gap-2">
                <span
                  className="inline-block w-2 h-2 rounded-full bg-[var(--color-accent)]"
                  aria-hidden="true"
                />
                {category.name}
              </h3>

              {/* Skill Bars */}
              <div className="space-y-1">
                {category.skills.map((skill, skillIndex) => (
                  <SkillBar
                    key={skill.name}
                    skill={skill}
                    isVisible={isInView && isRevealed}
                    delay={skillIndex * 0.1}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
