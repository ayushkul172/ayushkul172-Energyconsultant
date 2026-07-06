import { useRef, useState, useEffect, useCallback } from 'react';
import gsap from 'gsap';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { cn } from '@/utils/cn';
import type { Skill } from '@/types/index';

interface SkillBarProps {
  skill: Skill;
  /** Whether the bar should animate (controlled by parent via IntersectionObserver) */
  isVisible: boolean;
  /** Delay before this bar's animation starts (for stagger effect) */
  delay?: number;
}

/**
 * SkillBar — animated progress bar that fills from 0 → proficiency% over 1.5s ease-out.
 * Shows skill name, optional icon, and on hover displays a pulse-glow + numeric label.
 * Respects reduced motion: shows bar at final state immediately.
 */
export default function SkillBar({ skill, isVisible, delay = 0 }: SkillBarProps) {
  const barRef = useRef<HTMLDivElement>(null);
  const fillRef = useRef<HTMLDivElement>(null);
  const tweenRef = useRef<gsap.core.Tween | null>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);
  const reducedMotion = useReducedMotion();

  // Animate bar fill from 0 → target%
  const animateBar = useCallback(() => {
    if (!fillRef.current || hasAnimated) return;

    if (reducedMotion) {
      // Reduced motion: show final state immediately
      gsap.set(fillRef.current, { width: `${skill.proficiency}%` });
      setHasAnimated(true);
      return;
    }

    tweenRef.current = gsap.fromTo(
      fillRef.current,
      { width: '0%' },
      {
        width: `${skill.proficiency}%`,
        duration: 1.5,
        delay,
        ease: 'power2.out',
        onComplete: () => {
          setHasAnimated(true);
        },
      }
    );
  }, [skill.proficiency, delay, reducedMotion, hasAnimated]);

  // Pause animation when section leaves viewport
  const pauseAnimation = useCallback(() => {
    if (tweenRef.current && !hasAnimated) {
      tweenRef.current.pause();
    }
  }, [hasAnimated]);

  // Resume animation when section re-enters viewport
  const resumeAnimation = useCallback(() => {
    if (tweenRef.current && !hasAnimated) {
      tweenRef.current.resume();
    }
  }, [hasAnimated]);

  // Start or pause/resume based on visibility
  useEffect(() => {
    if (isVisible) {
      if (!tweenRef.current && !hasAnimated) {
        animateBar();
      } else {
        resumeAnimation();
      }
    } else {
      pauseAnimation();
    }
  }, [isVisible, animateBar, pauseAnimation, resumeAnimation, hasAnimated]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (tweenRef.current) {
        tweenRef.current.kill();
      }
    };
  }, []);

  return (
    <div
      ref={barRef}
      className={cn(
        'group relative flex items-center gap-3 py-2 px-3 rounded-lg transition-all duration-300',
        'hover:bg-[var(--color-card-surface)]',
        isHovered && 'shadow-[0_0_15px_rgba(6,182,212,0.3)]'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Skill icon */}
      {skill.icon && (
        <i
          className={cn(
            skill.icon,
            'w-5 text-center text-[var(--color-accent)] text-sm transition-transform duration-300',
            isHovered && 'scale-110'
          )}
          aria-hidden="true"
        />
      )}

      {/* Skill name and bar */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-body text-[var(--color-text)] truncate">
            {skill.name}
          </span>

          {/* Numeric label — visible on hover */}
          <span
            className={cn(
              'text-xs font-heading text-[var(--color-accent)] transition-opacity duration-300',
              isHovered ? 'opacity-100' : 'opacity-0'
            )}
            aria-label={`${skill.proficiency}% proficiency`}
          >
            {skill.proficiency}%
          </span>
        </div>

        {/* Progress bar track */}
        <div className="relative h-2 w-full rounded-full bg-[var(--color-background)] overflow-hidden">
          {/* Progress bar fill */}
          <div
            ref={fillRef}
            className={cn(
              'h-full rounded-full transition-shadow duration-300',
              'bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-accent-secondary)]',
              isHovered && 'shadow-[0_0_8px_rgba(6,182,212,0.6)]'
            )}
            style={{ width: reducedMotion ? `${skill.proficiency}%` : '0%' }}
            role="progressbar"
            aria-valuenow={skill.proficiency}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${skill.name} proficiency`}
          />
        </div>
      </div>

      {/* Pulse-glow overlay on hover */}
      {isHovered && !reducedMotion && (
        <div
          className="absolute inset-0 rounded-lg pointer-events-none animate-glow-pulse"
          style={{
            background: 'radial-gradient(ellipse at center, rgba(6,182,212,0.08) 0%, transparent 70%)',
          }}
        />
      )}
    </div>
  );
}
