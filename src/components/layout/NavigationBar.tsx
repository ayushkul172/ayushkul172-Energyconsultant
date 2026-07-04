import { useEffect, useRef, useState, useCallback } from 'react';
import gsap from 'gsap';
import type { NavItem } from '@/types';
import { cn } from '@/utils/cn';
import { smoothScrollTo } from '@/utils/smoothScroll';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { useTheme } from '@/hooks/useTheme';

export interface NavigationBarProps {
  items: NavItem[];
  activeIndex: number;
  onNavigate: (index: number) => void;
  isVisible: boolean;
}

const NAV_HEIGHT = 64;

/**
 * Fixed navigation bar with backdrop-blur, scroll-triggered visibility,
 * animated active indicator, mobile hamburger menu, theme toggle, and
 * keyboard accessibility.
 *
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
 */
export function NavigationBar({
  items,
  activeIndex,
  onNavigate,
  isVisible,
}: NavigationBarProps) {
  const navRef = useRef<HTMLElement>(null);
  const indicatorRef = useRef<HTMLDivElement>(null);
  const itemsRef = useRef<(HTMLButtonElement | null)[]>([]);
  const mobileMenuRef = useRef<HTMLDivElement>(null);

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const reducedMotion = useReducedMotion();
  const { toggleTheme, isDark } = useTheme();

  // ─── Slide-down visibility animation (400ms) ──────────────────────────────────
  useEffect(() => {
    const nav = navRef.current;
    if (!nav) return;

    if (reducedMotion) {
      nav.style.opacity = isVisible ? '1' : '0';
      nav.style.pointerEvents = isVisible ? 'auto' : 'none';
      return;
    }

    if (isVisible) {
      gsap.to(nav, {
        y: 0,
        opacity: 1,
        duration: 0.4,
        ease: 'power2.out',
        onStart: () => {
          nav.style.pointerEvents = 'auto';
        },
      });
    } else {
      gsap.to(nav, {
        y: -NAV_HEIGHT,
        opacity: 0,
        duration: 0.3,
        ease: 'power2.in',
        onComplete: () => {
          nav.style.pointerEvents = 'none';
        },
      });
    }
  }, [isVisible, reducedMotion]);

  // ─── Active indicator animation (300ms, power1.out) ───────────────────────────
  useEffect(() => {
    const indicator = indicatorRef.current;
    const activeItem = itemsRef.current[activeIndex];
    if (!indicator || !activeItem) return;

    const itemRect = activeItem.getBoundingClientRect();
    const navRect = navRef.current?.querySelector('ul')?.getBoundingClientRect();
    if (!navRect) return;

    const left = itemRect.left - navRect.left;
    const width = itemRect.width;

    if (reducedMotion) {
      indicator.style.left = `${left}px`;
      indicator.style.width = `${width}px`;
      return;
    }

    gsap.to(indicator, {
      left,
      width,
      duration: 0.3,
      ease: 'power1.out',
    });
  }, [activeIndex, reducedMotion, items]);

  // ─── Mobile menu staggered animation ──────────────────────────────────────────
  useEffect(() => {
    const menu = mobileMenuRef.current;
    if (!menu) return;

    if (mobileMenuOpen) {
      menu.style.display = 'flex';
      // Prevent body scroll while menu open
      document.body.style.overflow = 'hidden';

      if (reducedMotion) {
        menu.style.opacity = '1';
        return;
      }

      gsap.fromTo(
        menu,
        { opacity: 0 },
        { opacity: 1, duration: 0.3, ease: 'power2.out' }
      );

      // Stagger menu items (75ms between items)
      const menuItems = menu.querySelectorAll('[data-menu-item]');
      gsap.fromTo(
        menuItems,
        { opacity: 0, y: 20 },
        {
          opacity: 1,
          y: 0,
          duration: 0.3,
          stagger: 0.075,
          ease: 'power2.out',
          delay: 0.1,
        }
      );
    } else {
      document.body.style.overflow = '';

      if (reducedMotion) {
        menu.style.opacity = '0';
        setTimeout(() => {
          menu.style.display = 'none';
        }, 50);
        return;
      }

      gsap.to(menu, {
        opacity: 0,
        duration: 0.2,
        ease: 'power2.in',
        onComplete: () => {
          menu.style.display = 'none';
        },
      });
    }
  }, [mobileMenuOpen, reducedMotion]);

  // ─── Clean up body overflow on unmount ─────────────────────────────────────────
  useEffect(() => {
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  // ─── Navigation handler ────────────────────────────────────────────────────────
  const handleNavigate = useCallback(
    (index: number) => {
      // Close mobile menu first, then scroll
      if (mobileMenuOpen) {
        setMobileMenuOpen(false);
        // Small delay so menu close animation starts before scroll
        setTimeout(() => {
          onNavigate(index);
          smoothScrollTo(items[index].id, { offset: NAV_HEIGHT });
        }, 150);
      } else {
        onNavigate(index);
        smoothScrollTo(items[index].id, { offset: NAV_HEIGHT });
      }
    },
    [mobileMenuOpen, onNavigate, items]
  );

  // ─── Keyboard handler ──────────────────────────────────────────────────────────
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, index: number) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleNavigate(index);
      }
    },
    [handleNavigate]
  );

  return (
    <>
      {/* Fixed navigation bar */}
      <nav
        ref={navRef}
        className={cn(
          'fixed top-0 left-0 right-0 z-[1000]',
          'flex items-center justify-between px-6 lg:px-12',
          'border-b border-white/5'
        )}
        style={{
          height: `${NAV_HEIGHT}px`,
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          transform: `translateY(${isVisible ? 0 : -NAV_HEIGHT}px)`,
          opacity: isVisible ? 1 : 0,
          pointerEvents: isVisible ? 'auto' : 'none',
        }}
        role="navigation"
        aria-label="Main navigation"
      >
        {/* Logo / Brand */}
        <div className="flex items-center gap-2">
          <span
            className="text-xl font-heading font-bold tracking-tight"
            style={{ color: 'var(--color-accent, #06b6d4)' }}
          >
            AK
          </span>
        </div>

        {/* Desktop Navigation Links */}
        <div className="hidden md:block relative">
          <ul className="relative flex items-center gap-1" role="menubar">
            {/* Active indicator underline */}
            <div
              ref={indicatorRef}
              className="absolute bottom-0 h-0.5 rounded-full"
              style={{
                backgroundColor: 'var(--color-accent, #06b6d4)',
                transition: reducedMotion ? 'all 0.3s ease' : undefined,
              }}
              aria-hidden="true"
            />

            {items.map((item, index) => (
              <li key={item.id} role="none">
                <button
                  ref={(el) => {
                    itemsRef.current[index] = el;
                  }}
                  role="menuitem"
                  tabIndex={0}
                  className={cn(
                    'relative px-4 py-2 text-sm font-body font-medium',
                    'transition-colors duration-200 rounded-md',
                    'hover:text-[var(--color-accent)] focus-visible:outline-none',
                    'focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0f172a]',
                    index === activeIndex
                      ? 'text-[var(--color-accent)]'
                      : 'text-[var(--color-text-muted,#94a3b8)]'
                  )}
                  onClick={() => handleNavigate(index)}
                  onKeyDown={(e) => handleKeyDown(e, index)}
                  aria-current={index === activeIndex ? 'page' : undefined}
                >
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Right side: theme toggle + hamburger */}
        <div className="flex items-center gap-3">
          {/* Theme toggle button */}
          <button
            onClick={toggleTheme}
            className={cn(
              'p-2 rounded-lg transition-colors duration-200',
              'hover:bg-white/10 focus-visible:outline-none',
              'focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]'
            )}
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
            title={`Switch to ${isDark ? 'light' : 'dark'} theme`}
          >
            {isDark ? (
              // Sun icon (switch to light)
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
                className="text-[var(--color-accent,#06b6d4)]"
              >
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              // Moon icon (switch to dark)
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
                className="text-[var(--color-accent,#06b6d4)]"
              >
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          {/* Hamburger menu button (mobile only) */}
          <button
            className={cn(
              'md:hidden relative w-10 h-10 flex items-center justify-center',
              'rounded-lg transition-colors duration-200',
              'hover:bg-white/10 focus-visible:outline-none',
              'focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]'
            )}
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-menu"
          >
            {/* Animated hamburger → X lines */}
            <span className="sr-only">
              {mobileMenuOpen ? 'Close' : 'Open'} navigation menu
            </span>
            <span
              className={cn(
                'absolute w-5 h-0.5 rounded-full transition-all duration-300',
                'bg-[var(--color-text,#e2e8f0)]',
                mobileMenuOpen
                  ? 'rotate-45 translate-y-0'
                  : '-translate-y-1.5'
              )}
            />
            <span
              className={cn(
                'absolute w-5 h-0.5 rounded-full transition-all duration-300',
                'bg-[var(--color-text,#e2e8f0)]',
                mobileMenuOpen ? 'opacity-0 scale-0' : 'opacity-100 scale-100'
              )}
            />
            <span
              className={cn(
                'absolute w-5 h-0.5 rounded-full transition-all duration-300',
                'bg-[var(--color-text,#e2e8f0)]',
                mobileMenuOpen
                  ? '-rotate-45 translate-y-0'
                  : 'translate-y-1.5'
              )}
            />
          </button>
        </div>
      </nav>

      {/* Mobile Full-screen menu overlay */}
      <div
        ref={mobileMenuRef}
        id="mobile-menu"
        className={cn(
          'fixed inset-0 z-[999] flex-col items-center justify-center gap-6',
          'md:hidden'
        )}
        style={{
          display: 'none',
          backgroundColor: 'rgba(15, 23, 42, 0.97)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
        }}
        role="menu"
        aria-label="Mobile navigation menu"
      >
        {items.map((item, index) => (
          <button
            key={item.id}
            data-menu-item
            role="menuitem"
            tabIndex={mobileMenuOpen ? 0 : -1}
            className={cn(
              'text-2xl font-heading font-semibold px-6 py-3',
              'transition-colors duration-200 rounded-lg',
              'hover:text-[var(--color-accent)] focus-visible:outline-none',
              'focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]',
              index === activeIndex
                ? 'text-[var(--color-accent,#06b6d4)]'
                : 'text-[var(--color-text,#e2e8f0)]'
            )}
            onClick={() => handleNavigate(index)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            aria-current={index === activeIndex ? 'page' : undefined}
          >
            {item.label}
          </button>
        ))}

        {/* Theme toggle in mobile menu */}
        <button
          data-menu-item
          onClick={toggleTheme}
          className={cn(
            'mt-4 flex items-center gap-2 px-6 py-3 text-lg font-body',
            'text-[var(--color-text-muted,#94a3b8)] rounded-lg',
            'hover:text-[var(--color-accent)] transition-colors duration-200',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]'
          )}
          aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
        >
          {isDark ? (
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
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
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
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
          <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
      </div>
    </>
  );
}

export default NavigationBar;
