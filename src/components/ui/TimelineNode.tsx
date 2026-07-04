import { useRef, useState } from 'react';
import type { Experience } from '@/types/index';
import { cn } from '@/utils/cn';

export interface TimelineNodeProps {
  experience: Experience;
  index: number;
  /** 'left' or 'right' for alternating desktop layout */
  side: 'left' | 'right';
  /** Whether reduced motion is preferred */
  reducedMotion?: boolean;
}

/**
 * TimelineNode — a single entry in the experience timeline.
 *
 * Features:
 * - Scale-bounce entrance animation (0 → 1.2 → 1.0) with 200ms stagger
 * - Fade-and-slide-up for company/role details synced to timeline drawing
 * - Hover: expand node with morph transition (300ms) to show description
 * - Mobile: left-aligned in a single-column stacked layout
 */
export default function TimelineNode({
  experience,
  index,
  side,
  reducedMotion = false,
}: TimelineNodeProps) {
  const [isHovered, setIsHovered] = useState(false);
  const nodeRef = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={nodeRef}
      data-timeline-node
      data-index={index}
      className={cn(
        'timeline-node relative flex items-start gap-4 md:gap-8',
        // Desktop: alternating sides
        'md:w-1/2',
        side === 'left' ? 'md:self-start md:pr-12 md:text-right' : 'md:self-end md:pl-12 md:text-left',
        // Mobile: always left-aligned
        'w-full pl-12 text-left md:pl-0'
      )}
      style={{
        // Stagger delay for GSAP animation
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ['--stagger-delay' as any]: `${index * 200}ms`,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Node dot — the circle on the timeline */}
      <div
        data-timeline-dot
        className={cn(
          'absolute top-2 z-10 h-4 w-4 rounded-full bg-accent border-2 border-background',
          'transition-transform duration-300 ease-out',
          isHovered && !reducedMotion && 'scale-150',
          // Mobile: positioned on the left line
          'left-0 md:left-auto',
          // Desktop: positioned at the edge closest to center
          side === 'left' ? 'md:right-[-8px]' : 'md:left-[-8px]'
        )}
      />

      {/* Content card */}
      <div
        data-timeline-content
        className={cn(
          'rounded-lg border border-accent/20 bg-background-card p-4 md:p-6 w-full',
          'transition-all duration-300 ease-out',
          isHovered && 'border-accent/50 shadow-lg shadow-accent/10'
        )}
      >
        {/* Company logo placeholder + name */}
        <div className={cn(
          'flex items-center gap-3 mb-2',
          side === 'left' ? 'md:flex-row-reverse' : ''
        )}>
          {experience.logo ? (
            <img
              src={experience.logo}
              alt={`${experience.company} logo`}
              className="h-8 w-8 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/20 text-accent font-heading text-sm font-bold shrink-0">
              {experience.company.charAt(0)}
            </div>
          )}
          <h3 className="text-lg font-heading font-bold text-white">
            {experience.company}
          </h3>
        </div>

        {/* Role title */}
        <p className="text-accent font-body font-medium mb-1">
          {experience.title}
        </p>

        {/* Date */}
        <p className="text-sm text-gray-400 font-body mb-2">
          {experience.date}
        </p>

        {/* Description — shown on hover with morph transition */}
        <div
          className={cn(
            'overflow-hidden transition-all duration-300 ease-out',
            isHovered ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
          )}
        >
          <p className="text-sm text-gray-300 font-body leading-relaxed pt-2 border-t border-accent/10">
            {experience.description}
          </p>
        </div>
      </div>
    </div>
  );
}
