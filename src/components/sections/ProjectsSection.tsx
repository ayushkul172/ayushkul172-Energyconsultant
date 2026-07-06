import { useState, useCallback, useRef } from 'react';
import { spotlightProjects } from '@/data/projects';
import type { SpotlightProject } from '@/types';
import { ProjectOverlay } from '@/components/ui/ProjectOverlay';
import { cn } from '@/utils/cn';
import gsap from 'gsap';

/**
 * ProjectsSection — Full-width slide presentation format.
 * One project per screen, arrow navigation between projects.
 */
function ProjectsSection() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [expandedProject, setExpandedProject] = useState<SpotlightProject | null>(null);
  const [originRect, setOriginRect] = useState<DOMRect | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const slideRef = useRef<HTMLDivElement>(null);
  const totalSlides = spotlightProjects.length;

  const goToSlide = useCallback((index: number) => {
    if (isTransitioning || index === currentSlide) return;
    if (index < 0 || index >= totalSlides) return;

    setIsTransitioning(true);
    const slide = slideRef.current;
    if (slide) {
      gsap.to(slide, {
        opacity: 0,
        x: index > currentSlide ? -40 : 40,
        duration: 0.3,
        ease: 'power2.in',
        onComplete: () => {
          setCurrentSlide(index);
          gsap.fromTo(slide,
            { opacity: 0, x: index > currentSlide ? 40 : -40 },
            { opacity: 1, x: 0, duration: 0.4, ease: 'power2.out', onComplete: () => setIsTransitioning(false) }
          );
        },
      });
    } else {
      setCurrentSlide(index);
      setIsTransitioning(false);
    }
  }, [currentSlide, isTransitioning, totalSlides]);

  const goNext = useCallback(() => goToSlide((currentSlide + 1) % totalSlides), [currentSlide, totalSlides, goToSlide]);
  const goPrev = useCallback(() => goToSlide((currentSlide - 1 + totalSlides) % totalSlides), [currentSlide, totalSlides, goToSlide]);

  const handleExpand = useCallback((project: SpotlightProject, rect: DOMRect) => {
    setExpandedProject(project);
    setOriginRect(rect);
  }, []);

  const handleClose = useCallback(() => {
    setExpandedProject(null);
    setOriginRect(null);
  }, []);

  const project = spotlightProjects[currentSlide];

  return (
    <section
      id="projects"
      className="min-h-screen flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 overflow-hidden relative"
      style={{ backgroundColor: 'var(--color-background)' }}
    >
      {/* Section Header */}
      <div className="text-center mb-8">
        <span className="inline-block px-4 py-1.5 rounded-full text-xs font-semibold tracking-wider uppercase mb-3 bg-[var(--color-accent)]/10 text-[var(--color-accent)] border border-[var(--color-accent)]/20">
          Portfolio
        </span>
        <h2 className="text-3xl md:text-4xl lg:text-5xl font-heading font-bold text-[var(--color-text)]">
          Featured Projects
        </h2>
      </div>

      {/* Slide Content */}
      <div className="flex-1 max-w-7xl mx-auto w-full relative">
        <div ref={slideRef} className="w-full">
          <ProjectSlide
            project={project}
            index={currentSlide}
            total={totalSlides}
            onExpand={handleExpand}
          />
        </div>

        {/* Navigation Arrows */}
        <button
          onClick={goPrev}
          className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 sm:translate-x-0 z-20 w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center bg-white/5 border border-white/10 text-[var(--color-text)] hover:bg-[var(--color-accent)]/20 hover:border-[var(--color-accent)]/40 hover:text-[var(--color-accent)] transition-all duration-300 backdrop-blur-sm"
          aria-label="Previous project"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <button
          onClick={goNext}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 sm:translate-x-0 z-20 w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center bg-white/5 border border-white/10 text-[var(--color-text)] hover:bg-[var(--color-accent)]/20 hover:border-[var(--color-accent)]/40 hover:text-[var(--color-accent)] transition-all duration-300 backdrop-blur-sm"
          aria-label="Next project"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>

      {/* Slide Indicators */}
      <div className="flex justify-center gap-2 mt-6">
        {spotlightProjects.map((_, i) => (
          <button
            key={i}
            onClick={() => goToSlide(i)}
            className={cn(
              'h-2 rounded-full transition-all duration-300',
              i === currentSlide
                ? 'w-8 bg-[var(--color-accent)]'
                : 'w-2 bg-white/20 hover:bg-white/40'
            )}
            aria-label={`Go to project ${i + 1}`}
          />
        ))}
      </div>

      {/* Project Overlay */}
      {expandedProject && originRect && (
        <ProjectOverlay project={expandedProject} originRect={originRect} onClose={handleClose} />
      )}
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Individual Project Slide
// ═══════════════════════════════════════════════════════════════════════════════

interface ProjectSlideProps {
  project: SpotlightProject;
  index: number;
  total: number;
  onExpand: (project: SpotlightProject, rect: DOMRect) => void;
}

function ProjectSlide({ project, index, total, onExpand }: ProjectSlideProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const isUSCAgent = index === 0;

  const handleClick = useCallback(() => {
    if (cardRef.current) {
      onExpand(project, cardRef.current.getBoundingClientRect());
    }
  }, [project, onExpand]);

  return (
    <div
      ref={cardRef}
      className={cn(
        'relative rounded-2xl overflow-hidden cursor-pointer',
        'border border-white/[0.08] bg-[var(--color-card-surface)]/60 backdrop-blur-sm',
        'transition-all duration-300 hover:border-white/20'
      )}
      onClick={handleClick}
      data-project-card
      role="button"
      tabIndex={0}
      aria-label={`View details for ${project.title}`}
    >
      {/* Top accent bar */}
      <div className={cn('absolute top-0 left-0 right-0 h-1 project-border-glow')} />

      <div className="p-6 sm:p-8 lg:p-10">
        {/* Slide counter */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {isUSCAgent && (
              <>
                <span className="text-xl">⚡</span>
                <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[var(--color-accent)]/15 text-[var(--color-accent)] border border-[var(--color-accent)]/30 project-badge-animate">
                  Flagship ML Project
                </span>
              </>
            )}
          </div>
          <span className="text-xs text-[var(--color-text-muted)] font-mono">
            {String(index + 1).padStart(2, '0')} / {String(total).padStart(2, '0')}
          </span>
        </div>

        <div className="flex flex-col lg:flex-row gap-6 lg:gap-10">
          {/* Left: Image/Gallery */}
          <div className="lg:w-1/2">
            {isUSCAgent ? (
              /* USC Agent gets auto-scrolling gallery */
              <div className="relative rounded-xl overflow-hidden border border-white/[0.08] h-56 sm:h-64 lg:h-72 bg-[#0a0f1a]">
                <div className="usc-gallery flex h-full">
                  <img src="/images/usc-agent/USC agent 2.png" alt="USC Agent Dashboard" className="h-full w-full object-contain flex-shrink-0" loading="lazy" />
                  <img src="/images/usc-agent/USC agent 3.png" alt="Neural Network & ML Brain" className="h-full w-full object-contain flex-shrink-0" loading="lazy" />
                  <img src="/images/usc-agent/Gemini_Generated_Image_2yz0hq2yz0hq2yz0.png" alt="AI Analysis" className="h-full w-full object-contain flex-shrink-0" loading="lazy" />
                </div>
              </div>
            ) : index === 1 ? (
              /* Rig Tool gets auto-scrolling gallery */
              <div className="relative rounded-xl overflow-hidden border border-white/[0.08] h-56 sm:h-64 lg:h-72 bg-[#0a0f1a]">
                <div className="usc-gallery flex h-full">
                  <img src="/images/usc-agent/Rig tool 1.png" alt="Rig Tool Detailed Metrics" className="h-full w-full object-contain flex-shrink-0" loading="lazy" />
                  <img src="/images/usc-agent/Rig tool 2.png" alt="Monte Carlo Basin Simulator" className="h-full w-full object-contain flex-shrink-0" loading="lazy" />
                  <img src="/images/usc-agent/Rig tool 3.png" alt="Efficiency Overview Dashboard" className="h-full w-full object-contain flex-shrink-0" loading="lazy" />
                </div>
              </div>
            ) : (
              /* Other projects get single image */
              <div className="relative rounded-xl overflow-hidden border border-white/[0.08] h-56 sm:h-64 lg:h-72 bg-[#0a0f1a]">
                <img
                  src={project.image}
                  alt={project.title}
                  className="w-full h-full object-contain"
                  loading="lazy"
                />
              </div>
            )}
          </div>

          {/* Right: Content */}
          <div className="lg:w-1/2 flex flex-col">
            <div>
              <h3 className="text-2xl sm:text-3xl font-heading font-bold text-[var(--color-text)] mb-3">
                {project.title}
              </h3>

              {isUSCAgent ? (
                /* USC Agent: show full features in scrollable area */
                <div className="max-h-[40vh] overflow-y-auto pr-2 custom-scrollbar space-y-3 mb-4">
                  {parseActionContent(project.action).map((section, sIdx) => (
                    <div key={sIdx}>
                      {section.heading && (
                        <h4 className="text-xs font-heading font-bold text-[var(--color-accent)] mb-1.5">
                          {section.heading}
                        </h4>
                      )}
                      <ul className="space-y-1">
                        {section.bullets.map((bullet, bIdx) => (
                          <li key={bIdx} className="flex gap-1.5 text-xs text-[var(--color-text-subtle)] leading-relaxed">
                            <span className="text-[var(--color-accent)] mt-0.5 flex-shrink-0">•</span>
                            <span>{bullet}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                /* Other projects: show Challenge → Solution → Impact format */
                <div className="space-y-3 mb-5 max-h-[40vh] overflow-y-auto pr-2 custom-scrollbar">
                  {/* Challenge */}
                  <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/10 project-challenge-box">
                    <p className="text-[10px] uppercase tracking-wider text-red-400 font-bold mb-1">⚠ Challenge</p>
                    <p className="text-xs text-[var(--color-text-subtle)] leading-relaxed">{project.situation}</p>
                  </div>
                  {/* Solution */}
                  <div className="p-3 rounded-lg bg-[var(--color-accent)]/5 border border-[var(--color-accent)]/10 project-solution-box">
                    <p className="text-[10px] uppercase tracking-wider text-[var(--color-accent)] font-bold mb-1">💡 Solution</p>
                    <div className="text-xs text-[var(--color-text-subtle)] leading-relaxed space-y-1">
                      {project.action.split('\n').filter(l => l.trim()).map((line, i) => {
                        const cleaned = line.replace(/^[•▸\-]\s*/, '').trim();
                        return cleaned ? (
                          <p key={i} className="flex gap-1.5">
                            <span className="text-[var(--color-accent)] flex-shrink-0">▸</span>
                            <span>{cleaned}</span>
                          </p>
                        ) : null;
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* Tech stack — animated pills */}
              <div className="flex flex-wrap gap-2 mb-5">
                {project.techStack.map((tech, i) => (
                  <span
                    key={tech}
                    className="text-xs px-3 py-1.5 rounded-full font-medium bg-white/5 text-[var(--color-text-subtle)] border border-white/10 project-tech-pill"
                    style={{ animationDelay: `${i * 80}ms` }}
                  >
                    {tech}
                  </span>
                ))}
              </div>

              {/* GitHub link for USC Agent */}
              {isUSCAgent && (
                <a
                  href="https://github.com/ayushkul172/USC-TOO-AGENT-"
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white/5 border border-white/10 text-[var(--color-text-subtle)] hover:border-[var(--color-accent)]/40 hover:text-[var(--color-accent)] transition-all duration-300 mb-4"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  View on GitHub
                </a>
              )}
              {/* Live Demo link for Rig Tool (index 1) */}
              {index === 1 && (
                <a
                  href="https://rogtooleffeciency.streamlit.app/"
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white/5 border border-white/10 text-[var(--color-text-subtle)] hover:border-green-500/40 hover:text-green-400 transition-all duration-300 mb-4"
                >
                  <span>▶</span>
                  Live Demo
                </a>
              )}
            </div>

            {/* Impact Metrics — bold and eye-catching */}
            <div className="grid grid-cols-3 gap-3">
              {project.results.map((result, i) => (
                <div
                  key={i}
                  className="text-center p-3 sm:p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-[var(--color-accent)]/30 transition-all duration-300 group/stat"
                >
                  <span className={cn(
                    'block text-2xl sm:text-3xl lg:text-4xl font-bold mb-1 project-metric-glow',
                    'bg-gradient-to-r bg-clip-text text-transparent',
                    'group-hover/stat:drop-shadow-[0_0_12px_rgba(6,182,212,0.5)]',
                    project.accentColor
                  )}>
                    {result.metric}
                  </span>
                  <span className="text-[10px] sm:text-xs text-[var(--color-text-muted)] leading-tight block">
                    {result.description}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProjectsSection;

// ═══════════════════════════════════════════════════════════════════════════════
// Utility: parse structured action content into sections
// ═══════════════════════════════════════════════════════════════════════════════

function parseActionContent(text: string): { heading: string | null; bullets: string[] }[] {
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  const sections: { heading: string | null; bullets: string[] }[] = [];
  let current: { heading: string | null; bullets: string[] } = { heading: null, bullets: [] };

  for (const line of lines) {
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
