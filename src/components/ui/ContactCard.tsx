import { useRef, useCallback } from 'react';
import type { ContactMethod } from '@/types';
import { cn } from '@/utils/cn';

export interface ContactCardProps {
  contact: ContactMethod;
  index: number;
}

/**
 * Interactive contact card with hover float effect (translateY -8px + elevated shadow),
 * click ripple animation (400ms), and reverse hover on cursor leave (300ms).
 *
 * Requirements: 8.2, 8.4, 8.5
 */
export function ContactCard({ contact, index }: ContactCardProps) {
  const cardRef = useRef<HTMLAnchorElement>(null);

  // ─── Click Ripple Animation ────────────────────────────────────────────────────
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>) => {
      const card = cardRef.current;
      if (!card) return;

      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Create ripple span at click coordinates
      const ripple = document.createElement('span');
      ripple.className = 'contact-card-ripple';
      ripple.style.left = `${x}px`;
      ripple.style.top = `${y}px`;
      card.appendChild(ripple);

      // Remove ripple after animation completes (400ms)
      setTimeout(() => {
        ripple.remove();
      }, 400);
    },
    []
  );

  return (
    <a
      ref={cardRef}
      href={contact.href}
      target={contact.type === 'linkedin' || contact.type === 'website' ? '_blank' : undefined}
      rel={
        contact.type === 'linkedin' || contact.type === 'website'
          ? 'noopener noreferrer'
          : undefined
      }
      onClick={handleClick}
      className={cn(
        'contact-card group relative block overflow-hidden rounded-xl p-6',
        'border border-white/10 bg-[var(--color-card-surface)]',
        'transition-all duration-300 ease-out',
        'hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(0,0,0,0.3)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]',
        'focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-background)]'
      )}
      style={{ willChange: 'transform, box-shadow' }}
      data-contact-card
      data-index={index}
      aria-label={`${contact.label}: ${contact.value}`}
    >
      {/* Accent gradient overlay on hover */}
      <div
        className={cn(
          'absolute inset-0 opacity-0 transition-opacity duration-300',
          'group-hover:opacity-10',
          `bg-gradient-to-br ${contact.accentColor}`
        )}
        aria-hidden="true"
      />

      {/* Icon */}
      <div
        className={cn(
          'mb-4 flex h-12 w-12 items-center justify-center rounded-lg',
          `bg-gradient-to-br ${contact.accentColor}`,
          'text-white text-xl shadow-lg'
        )}
      >
        <i className={contact.icon} aria-hidden="true" />
      </div>

      {/* Label */}
      <h3 className="text-lg font-heading font-semibold text-[var(--color-text)] mb-1">
        {contact.label}
      </h3>

      {/* Value */}
      <p className="text-sm text-[var(--color-text-subtle)] break-all">
        {contact.value}
      </p>

      {/* Arrow indicator */}
      <div
        className={cn(
          'absolute top-6 right-6 opacity-0 translate-x-1',
          'transition-all duration-300',
          'group-hover:opacity-100 group-hover:translate-x-0',
          'text-[var(--color-accent)]'
        )}
        aria-hidden="true"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="7" y1="17" x2="17" y2="7" />
          <polyline points="7 7 17 7 17 17" />
        </svg>
      </div>
    </a>
  );
}

export default ContactCard;
