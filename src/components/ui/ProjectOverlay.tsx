import { useRef, useEffect, useCallback } from 'react';
import gsap from 'gsap';
import type { SpotlightProject } from '@/types';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { cn } from '@/utils/cn';

export interface ProjectOverlayProps {
  project: SpotlightProject;
  originRect: DOMRect;
  onClose: () => void;
}

/**
 * ProjectOverlay — expanded detail view showing full STAR details
 * (situation, task, action, results) and tech stack.
 *
 * Features:
 * - GSAP Flip-style animation from card rect to centered overlay
 * - Focus trap (Tab cycles within overlay)
 * - Escape key or click-outside dismissal (400ms reverse animation)
 * - Returns focus to originating card on close
 *
 * Requirements: 4.3, 4.5, 4.6
 */
export function ProjectOverlay({ project, originRect, onClose }: ProjectOverlayProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useReducedMotion();
  const firstFocusableRef = useRef<HTMLButtonElement>(null);
  const lastFocusableRef = useRef<HTMLButtonElement>(null);
  const isClosing = useRef(false);

  // ─── Entry animation ───────────────────────────────────────────────────────
  useEffect(() => {
    const content = contentRef.current;
    const backdrop = backdropRef.current;
    if (!content || !backdrop) return;

    if (prefersReducedMotion) {
      // Just show immediately with simple opacity
      gsap.set(backdrop, { opacity: 1 });
      gsap.set(content, { opacity: 1, scale: 1, x: 0, y: 0 });
      return;
    }

    // Calculate starting transform based on originRect
    const viewportW = window.innerWidth;
    const viewportH = window.innerHeight;

    // Final content position: centered
    const finalWidth = Math.min(viewportW * 0.9, 800);
    const finalHeight = Math.min(viewportH * 0.85, 700);
    const finalX = (viewportW - finalWidth) / 2;
    const finalY = (viewportH - finalHeight) / 2;

    // Calculate starting offsets from center
    const startX = originRect.left + originRect.width / 2 - (finalX + finalWidth / 2);
    const startY = originRect.top + originRect.height / 2 - (finalY + finalHeight / 2);
    const startScale = Math.min(originRect.width / finalWidth, originRect.height / finalHeight);

    // Animate backdrop
    gsap.fromTo(backdrop, { opacity: 0 }, { opacity: 1, duration: 0.3, ease: 'power2.out' });

    // Animate content from card position to center
    gsap.fromTo(
      content,
      {
        opacity: 0,
        scale: startScale,
        x: startX,
        y: startY,
      },
      {
        opacity: 1,
        scale: 1,
        x: 0,
        y: 0,
        duration: 0.5,
        ease: 'power2.out',
      }
    );
  }, [originRect, prefersReducedMotion]);

  // ─── Close with reverse animation ─────────────────────────────────────────
  const handleClose = useCallback(() => {
    if (isClosing.current) return;
    isClosing.current = true;

    const content = contentRef.current;
    const backdrop = backdropRef.current;

    if (!content || !backdrop || prefersReducedMotion) {
      onClose();
      return;
    }

    // Calculate reverse animation target
    const viewportW = window.innerWidth;
    const viewportH = window.innerHeight;
    const finalWidth = Math.min(viewportW * 0.9, 800);
    const finalHeight = Math.min(viewportH * 0.85, 700);
    const finalX = (viewportW - finalWidth) / 2;
    const finalY = (viewportH - finalHeight) / 2;

    const endX = originRect.left + originRect.width / 2 - (finalX + finalWidth / 2);
    const endY = originRect.top + originRect.height / 2 - (finalY + finalHeight / 2);
    const endScale = Math.min(originRect.width / finalWidth, originRect.height / finalHeight);

    // Reverse animation (400ms)
    gsap.to(backdrop, { opacity: 0, duration: 0.4, ease: 'power2.in' });
    gsap.to(content, {
      opacity: 0,
      scale: endScale,
      x: endX,
      y: endY,
      duration: 0.4,
      ease: 'power2.in',
      onComplete: () => {
        onClose();
      },
    });
  }, [onClose, originRect, prefersReducedMotion]);

  // ─── Escape key handler ────────────────────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleClose]);

  // ─── Focus trap ────────────────────────────────────────────────────────────
  useEffect(() => {
    // Focus the close button on mount
    firstFocusableRef.current?.focus();

    const handleTabTrap = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const overlay = overlayRef.current;
      if (!overlay) return;

      const focusableElements = overlay.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      if (focusableElements.length === 0) return;

      const first = focusableElements[0];
      const last = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        // Shift+Tab: if on first, go to last
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        // Tab: if on last, go to first
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleTabTrap);
    return () => document.removeEventListener('keydown', handleTabTrap);
  }, []);

  // ─── Click outside (backdrop click) ────────────────────────────────────────
  const handleBackdropClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        handleClose();
      }
    },
    [handleClose]
  );

  // ─── Glow accent mapping ──────────────────────────────────────────────────
  const accentRgb = getAccentRgb(project.accentColor);

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label={`Project details: ${project.title}`}
    >
      {/* Backdrop */}
      <div
        ref={backdropRef}
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleBackdropClick}
        style={{ opacity: prefersReducedMotion ? 1 : 0 }}
        aria-hidden="true"
      />

      {/* Content Panel */}
      <div
        ref={contentRef}
        className={cn(
          'relative w-[90vw] max-w-[800px] max-h-[85vh] overflow-y-auto',
          'rounded-2xl border border-white/10 bg-[var(--color-card-surface)]',
          'shadow-2xl p-6 sm:p-8'
        )}
        style={{
          opacity: prefersReducedMotion ? 1 : 0,
          boxShadow: `0 0 60px ${accentRgb}30, 0 25px 50px rgba(0,0,0,0.5)`,
        }}
      >
        {/* Close Button */}
        <button
          ref={firstFocusableRef}
          onClick={handleClose}
          className={cn(
            'absolute top-4 right-4 z-10',
            'w-10 h-10 rounded-full flex items-center justify-center',
            'bg-white/10 hover:bg-white/20 transition-colors duration-200',
            'text-[var(--color-text)] hover:text-white',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]'
          )}
          aria-label="Close project details"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* Project Image */}
        <div className="rounded-xl overflow-hidden mb-6 h-48 sm:h-56">
          <img
            src={project.image}
            alt={project.title}
            className="w-full h-full object-cover"
          />
        </div>

        {/* Title */}
        <h2 className="text-2xl sm:text-3xl font-heading font-bold text-[var(--color-text)] mb-4">
          {project.title}
        </h2>

        {/* Tech Stack */}
        <div className="flex flex-wrap gap-2 mb-6">
          {project.techStack.map((tech) => (
            <span
              key={tech}
              className={cn(
                'text-sm px-3 py-1 rounded-full',
                'bg-gradient-to-r bg-clip-text text-transparent font-medium',
                project.accentColor,
                'border border-[var(--color-accent)]/30 !text-[var(--color-accent)]'
              )}
            >
              {tech}
            </span>
          ))}
        </div>

        {/* STAR Details */}
        <div className="space-y-4 mb-6">
          <StarSection label="Situation" content={project.situation} />
          <StarSection label="Task" content={project.task} />
          <StarSection label="Action" content={project.action} />
        </div>

        {/* Results */}
        <div>
          <h3 className="text-sm font-heading font-semibold text-[var(--color-text-subtle)] uppercase tracking-wider mb-3">
            Key Results
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {project.results.map((result, i) => (
              <div
                key={i}
                className="text-center p-4 rounded-lg bg-white/5 border border-white/5"
              >
                <span
                  className={cn(
                    'block text-2xl font-bold mb-1',
                    'bg-gradient-to-r bg-clip-text text-transparent',
                    project.accentColor
                  )}
                >
                  {result.metric}
                </span>
                <span className="text-xs text-[var(--color-text-subtle)] leading-tight">
                  {result.description}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom close button (for focus trap target) */}
        <button
          ref={lastFocusableRef}
          onClick={handleClose}
          className={cn(
            'mt-6 w-full py-3 rounded-lg font-heading font-semibold text-sm',
            'bg-[var(--color-accent)] text-[var(--color-background)]',
            'hover:bg-[var(--color-accent-secondary)] transition-colors duration-200',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]'
          )}
        >
          Close
        </button>
      </div>
    </div>
  );
}

// ─── StarSection sub-component ───────────────────────────────────────────────

function StarSection({ label, content }: { label: string; content: string }) {
  // Check if content has sections (emoji headings + bullet points)
  const hasStructuredContent = content.includes('🤖') || content.includes('🧠') || content.includes('📋') || content.includes('🔔') || content.includes('💬') || content.includes('📊') || content.includes('🏗️') || content.includes('⚙️') || content.includes('🧪');

  if (hasStructuredContent) {
    return (
      <div>
        <h3 className="text-sm font-heading font-semibold text-[var(--color-text-subtle)] uppercase tracking-wider mb-3">
          {label}
        </h3>
        <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-2 custom-scrollbar">
          {parseStructuredContent(content).map((section, idx) => (
            <div key={idx}>
              {section.heading && (
                <h4 className="text-xs font-heading font-bold text-[var(--color-accent)] mb-1.5 flex items-center gap-1.5">
                  {section.heading}
                </h4>
              )}
              <ul className="space-y-1">
                {section.bullets.map((bullet, bIdx) => (
                  <li key={bIdx} className="flex gap-2 text-xs text-[var(--color-text-subtle)] leading-relaxed">
                    <span className="text-[var(--color-accent)] mt-0.5 flex-shrink-0">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-heading font-semibold text-[var(--color-text-subtle)] uppercase tracking-wider mb-1">
        {label}
      </h3>
      <p className="text-sm text-[var(--color-text)] leading-relaxed">
        {content}
      </p>
    </div>
  );
}

function parseStructuredContent(text: string): { heading: string | null; bullets: string[] }[] {
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  const sections: { heading: string | null; bullets: string[] }[] = [];
  let current: { heading: string | null; bullets: string[] } = { heading: null, bullets: [] };

  for (const line of lines) {
    // Lines starting with emoji are section headings
    if (/^[🤖🧠📋🔔💬📊🏗️⚙️🧪]/.test(line) && !line.startsWith('•')) {
      if (current.heading || current.bullets.length > 0) sections.push(current);
      current = { heading: line, bullets: [] };
    } else {
      const cleaned = line.replace(/^[•▸\-]\s*/, '').trim();
      if (cleaned.length > 0) current.bullets.push(cleaned);
    }
  }

  if (current.heading || current.bullets.length > 0) sections.push(current);
  return sections;
}

// ─── Utility: Extract RGB from accent gradient class ─────────────────────────

function getAccentRgb(accentColor: string): string {
  const map: Record<string, string> = {
    'from-cyan-500': '6, 182, 212',
    'from-purple-500': '168, 85, 247',
    'from-green-500': '34, 197, 94',
    'from-orange-500': '249, 115, 22',
  };

  const fromClass = accentColor.split(' ').find((cls) => cls.startsWith('from-'));
  return (fromClass && map[fromClass]) || '6, 182, 212';
}

export default ProjectOverlay;
