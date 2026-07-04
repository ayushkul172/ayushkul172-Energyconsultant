import { useState, useEffect, useRef, useCallback } from 'react';
import { registerPlugins } from '@/animation/engine';
import { useTheme } from '@/hooks/useTheme';
import { useOrientationChange } from '@/hooks/useOrientationChange';
import { useSwipeGesture } from '@/hooks/useSwipeGesture';
import { navigationItems } from '@/data/navigation';
import Preloader from '@/components/layout/Preloader';
import NavigationBar from '@/components/layout/NavigationBar';
import PageTurner from '@/components/layout/PageTurner';
import HeroSection from '@/components/sections/HeroSection';
import ServicesSection from '@/components/sections/ServicesSection';
import ProjectsSection from '@/components/sections/ProjectsSection';
import ExperienceSection from '@/components/sections/ExperienceSection';
import SkillsSection from '@/components/sections/SkillsSection';
import ContactSection from '@/components/sections/ContactSection';

/**
 * App shell component — orchestrates:
 * Preloader → ThemeManager → NavigationBar → PageTurner with section children.
 *
 * Manages global state: current page, theme, loading state.
 * Touch gesture support: swipe left/right (≥50px horizontal) for page navigation.
 */
function App() {
  // ─── Global State ──────────────────────────────────────────────────────────
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const [navVisible, setNavVisible] = useState(false);

  // ─── Theme ─────────────────────────────────────────────────────────────────
  // Theme management — theme is used for data-theme attribute
  const { theme } = useTheme();

  // ─── Orientation Change Handler ────────────────────────────────────────────
  // Recalculates layout within 300ms of orientation change (debounced)
  // The returned key forces re-renders of children when orientation changes
  const orientationKey = useOrientationChange();

  const containerRef = useRef<HTMLDivElement>(null);

  // ─── Register GSAP Plugins on Mount ────────────────────────────────────────
  useEffect(() => {
    registerPlugins();
  }, []);

  // ─── Preloader Complete Handler ────────────────────────────────────────────
  const handlePreloaderComplete = useCallback(() => {
    setIsLoading(false);
    // Show navigation bar after preloader finishes
    setNavVisible(true);
  }, []);

  // ─── Page Navigation ───────────────────────────────────────────────────────
  const totalPages = navigationItems.length;

  const navigateToPage = useCallback(
    (pageIndex: number) => {
      if (pageIndex >= 0 && pageIndex < totalPages) {
        setCurrentPage(pageIndex);
      }
    },
    [totalPages]
  );

  // ─── Scroll-Spy: Update activeIndex based on viewport section ──────────────
  useEffect(() => {
    if (isLoading) return;

    const sectionIds = navigationItems.map((item) => item.id);
    const observers: IntersectionObserver[] = [];

    sectionIds.forEach((id, index) => {
      const element = document.getElementById(id);
      if (!element) return;

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setCurrentPage(index);
            }
          });
        },
        { threshold: 0.5 }
      );

      observer.observe(element);
      observers.push(observer);
    });

    return () => {
      observers.forEach((obs) => obs.disconnect());
    };
  }, [isLoading]);

  // ─── Touch Gesture: Swipe Left/Right ≥50px for Page Navigation ─────────────
  const swipeHandlers = useSwipeGesture({
    onSwipe: useCallback(
      (direction: 'left' | 'right') => {
        if (direction === 'left') {
          navigateToPage(currentPage + 1);
        } else {
          navigateToPage(currentPage - 1);
        }
      },
      [currentPage, navigateToPage]
    ),
  });

  // ─── Render ────────────────────────────────────────────────────────────────

  if (isLoading) {
    return <Preloader onComplete={handlePreloaderComplete} />;
  }

  return (
    <div
      ref={containerRef}
      className="min-h-screen max-w-full overflow-x-hidden"
      data-theme={theme}
      data-orientation-key={orientationKey}
      {...swipeHandlers}
    >
      {/* Navigation Bar */}
      <NavigationBar
        items={navigationItems}
        activeIndex={currentPage}
        onNavigate={navigateToPage}
        isVisible={navVisible}
      />

      {/* Page Turner with Section Placeholders */}
      <PageTurner currentPage={currentPage} onPageChange={setCurrentPage}>
        <HeroSection isRevealed={!isLoading} onNavigate={navigateToPage} />
        <ServicesSection />
        <ProjectsSection />
        <ExperienceSection />
        <SkillsSection />
        <ContactSection />
      </PageTurner>
    </div>
  );
}

export default App;
