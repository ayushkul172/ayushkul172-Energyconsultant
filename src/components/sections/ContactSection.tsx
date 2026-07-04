import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { contactMethods } from '@/data/contact';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { useScrollAnimation } from '@/hooks/useScrollAnimation';
import { useSplitTextReveal } from '@/hooks/useSplitTextReveal';
import { ContactCard } from '@/components/ui/ContactCard';
import { cn } from '@/utils/cn';

/**
 * Contact section with staggered 3D flip-in entrance animation (150ms delays,
 * 600ms per card), animated gradient mesh background (10s loop), and
 * interactive contact cards.
 *
 * Uses GSAP for flip-in entrance animations triggered by IntersectionObserver.
 * CSS handles hover effects and gradient mesh background.
 * Reduced motion: simple opacity fade instead of 3D flip-in.
 *
 * Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
 */
export function ContactSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const cardsContainerRef = useRef<HTMLDivElement>(null);
  const hasAnimated = useRef(false);
  const reducedMotion = useReducedMotion();

  // Split-text reveal for section heading
  const headingRef = useRef<HTMLHeadingElement>(null);
  const { isRevealed: _headingRevealed } = useSplitTextReveal(headingRef);

  // Scroll animation for subtitle paragraph (Requirement 2.1)
  const { ref: subtitleRef } = useScrollAnimation({
    type: 'fadeInUp',
    options: { threshold: 0.2, duration: 0.6 },
  });

  useEffect(() => {
    const section = sectionRef.current;
    const container = cardsContainerRef.current;
    if (!section || !container) return;

    // IntersectionObserver triggers flip-in animation
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated.current) {
            hasAnimated.current = true;
            animateCards(container);
          }
        });
      },
      { threshold: 0.2 }
    );

    observer.observe(section);

    return () => {
      observer.disconnect();
    };
  }, [reducedMotion]);

  const animateCards = (container: HTMLDivElement) => {
    const cards = container.querySelectorAll('[data-contact-card]');

    if (reducedMotion) {
      // Simple opacity fade for reduced motion
      gsap.fromTo(
        cards,
        { opacity: 0 },
        {
          opacity: 1,
          duration: 0.3,
          stagger: 0.05,
          ease: 'none',
        }
      );
      return;
    }

    // 3D flip-in animation: 600ms per card, 150ms stagger delay
    gsap.fromTo(
      cards,
      {
        opacity: 0,
        rotateY: -90,
        transformPerspective: 1200,
      },
      {
        opacity: 1,
        rotateY: 0,
        transformPerspective: 1200,
        duration: 0.6,
        stagger: 0.15,
        ease: 'power2.out',
      }
    );
  };

  return (
    <section
      ref={sectionRef}
      id="contact"
      className="relative min-h-screen flex items-center justify-center py-20 px-4 sm:px-6 lg:px-8 overflow-hidden"
      aria-labelledby="contact-heading"
    >
      {/* Animated gradient mesh background (10s loop, 3-4 accent color positions) */}
      <div
        className="contact-gradient-mesh absolute inset-0 pointer-events-none"
        aria-hidden="true"
      />

      {/* Content */}
      <div className="relative z-10 w-full max-w-4xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-12">
          <h2
            id="contact-heading"
            ref={headingRef}
            className="text-3xl sm:text-4xl lg:text-5xl font-heading font-bold text-[var(--color-text)] mb-4"
          >
            Get In Touch
          </h2>
          <p ref={subtitleRef as unknown as React.RefObject<HTMLParagraphElement>} className="text-base sm:text-lg text-[var(--color-text-subtle)] max-w-2xl mx-auto">
            Ready to collaborate? Reach out through any of the channels below.
          </p>
        </div>

        {/* Contact cards grid */}
        <div
          ref={cardsContainerRef}
          className={cn(
            'grid gap-6',
            'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
          )}
        >
          {contactMethods.map((contact, index) => (
            <ContactCard
              key={contact.type}
              contact={contact}
              index={index}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export default ContactSection;
