import { useRef, useEffect } from 'react';
import gsap from 'gsap';
import { experiences } from '@/data/experience';
import { useReducedMotion } from '@/hooks/useReducedMotion';

/**
 * ExperienceSection — Vertical timeline with all details visible.
 * Animated on scroll, no hover required. Full bullet points and sections shown.
 */
export default function ExperienceSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const nodesRef = useRef<(HTMLDivElement | null)[]>([]);
  const lineRef = useRef<HTMLDivElement>(null);
  const reducedMotion = useReducedMotion();
  const animatedRef = useRef(false);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section || animatedRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !animatedRef.current) {
            animatedRef.current = true;
            animateTimeline();
            observer.disconnect();
          }
        });
      },
      { threshold: 0.1 }
    );

    observer.observe(section);
    return () => observer.disconnect();
  }, []);

  const animateTimeline = () => {
    if (reducedMotion) {
      // Show everything immediately
      if (lineRef.current) lineRef.current.style.height = '100%';
      nodesRef.current.forEach(node => {
        if (node) gsap.set(node, { opacity: 1, y: 0 });
      });
      return;
    }

    // Animate the line growing
    if (lineRef.current) {
      gsap.fromTo(lineRef.current, { height: '0%' }, { height: '100%', duration: 2, ease: 'power2.inOut' });
    }

    // Stagger each experience node
    nodesRef.current.forEach((node, i) => {
      if (!node) return;
      gsap.fromTo(node,
        { opacity: 0, y: 40, scale: 0.97 },
        { opacity: 1, y: 0, scale: 1, duration: 0.7, delay: 0.3 + i * 0.4, ease: 'power2.out' }
      );
    });
  };

  return (
    <section
      ref={sectionRef}
      id="experience"
      className="py-16 sm:py-20 px-4 sm:px-6 lg:px-8 overflow-y-auto overflow-x-hidden"
      style={{ backgroundColor: 'var(--color-background)' }}
      aria-label="Professional Experience"
    >
      {/* Section Header */}
      <div className="text-center mb-12">
        <span className="inline-block px-4 py-1.5 rounded-full text-xs font-semibold tracking-wider uppercase mb-3 bg-[var(--color-accent)]/10 text-[var(--color-accent)] border border-[var(--color-accent)]/20">
          Career Journey
        </span>
        <h2 className="text-3xl md:text-4xl lg:text-5xl font-heading font-bold text-[var(--color-text)]">
          Professional Experience
        </h2>
      </div>

      {/* Timeline */}
      <div className="max-w-5xl mx-auto relative">
        {/* Vertical line */}
        <div className="absolute left-4 sm:left-8 top-0 bottom-0 w-[2px]">
          <div
            ref={lineRef}
            className="w-full bg-gradient-to-b from-[var(--color-accent)] via-[var(--color-accent-secondary)] to-[var(--color-accent)]/30 rounded-full"
            style={{ height: reducedMotion ? '100%' : '0%' }}
          />
        </div>

        {/* Experience Nodes */}
        <div className="space-y-10">
          {experiences.map((exp, i) => (
            <div
              key={i}
              ref={(el) => { nodesRef.current[i] = el; }}
              className="relative pl-12 sm:pl-20"
              style={{ opacity: reducedMotion ? 1 : 0 }}
            >
              {/* Timeline dot */}
              <div className="absolute left-[10px] sm:left-[26px] top-6 w-4 h-4 rounded-full bg-[var(--color-accent)] border-[3px] border-[var(--color-background)] shadow-[0_0_10px_rgba(6,182,212,0.5)] z-10" />

              {/* Card */}
              <div className="rounded-xl border border-white/[0.08] bg-[var(--color-card-surface)]/70 backdrop-blur-sm overflow-hidden">
                {/* Top accent */}
                <div className="h-[2px] bg-gradient-to-r from-[var(--color-accent)] to-transparent" />

                <div className="p-5 sm:p-6">
                  {/* Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-[var(--color-accent)]/15 flex items-center justify-center text-[var(--color-accent)] font-heading font-bold text-sm flex-shrink-0">
                        {exp.company.charAt(0)}
                      </div>
                      <div>
                        <h3 className="text-lg sm:text-xl font-heading font-bold text-[var(--color-text)]">
                          {exp.company}
                        </h3>
                        <p className="text-[var(--color-accent)] font-medium text-sm">
                          {exp.title}
                        </p>
                      </div>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-white/5 border border-white/10 text-[var(--color-text-muted)] self-start sm:self-auto">
                      {exp.date}
                    </span>
                  </div>

                  {/* Formatted description with sections */}
                  <div className="space-y-4">
                    {parseDescription(exp.description).map((section, sIdx) => (
                      <div key={sIdx}>
                        {section.heading && (
                          <h4 className="text-xs font-heading font-bold uppercase tracking-wider text-[var(--color-accent)] mb-2 flex items-center gap-2">
                            <span className="w-4 h-[2px] bg-[var(--color-accent)] rounded" />
                            {section.heading}
                          </h4>
                        )}
                        <ul className="space-y-1.5">
                          {section.bullets.map((bullet, bIdx) => (
                            <li key={bIdx} className="flex gap-2 text-xs sm:text-sm text-[var(--color-text-subtle)] leading-relaxed">
                              <span className="text-[var(--color-accent)] mt-0.5 flex-shrink-0 text-[10px]">▸</span>
                              <span dangerouslySetInnerHTML={{ __html: highlightKeyMetrics(bullet) }} />
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════════════════════════════════════

interface DescriptionSection {
  heading: string | null;
  bullets: string[];
}

function parseDescription(desc: string): DescriptionSection[] {
  const lines = desc.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  const sections: DescriptionSection[] = [];
  let currentSection: DescriptionSection = { heading: null, bullets: [] };

  for (const line of lines) {
    if (isHeading(line)) {
      if (currentSection.heading || currentSection.bullets.length > 0) {
        sections.push(currentSection);
      }
      currentSection = { heading: cleanHeading(line), bullets: [] };
    } else {
      const cleaned = line.replace(/^[•▸\-]\s*/, '').trim();
      if (cleaned.length > 0) {
        currentSection.bullets.push(cleaned);
      }
    }
  }

  if (currentSection.heading || currentSection.bullets.length > 0) {
    sections.push(currentSection);
  }

  return sections;
}

function isHeading(line: string): boolean {
  const cleaned = line.replace(/[🚀🤖⚡📊]/g, '').trim();
  if (/^[A-Z\s&/,()]+$/.test(cleaned) && cleaned.length < 60) return true;
  if (/^[🚀🤖⚡📊]/.test(line) && !line.startsWith('•')) return true;
  return false;
}

function cleanHeading(line: string): string {
  return line.replace(/^[•▸\-]\s*/, '').trim();
}

function highlightKeyMetrics(text: string): string {
  let h = text;
  h = h.replace(/(\d+%\+?)/g, '<span class="text-[var(--color-accent)] font-semibold">$1</span>');
  h = h.replace(/(\$[\d,.]+(M|B|K)?(-\$?[\d,.]+(M|B|K)?)?)/g, '<span class="text-[var(--color-accent)] font-semibold">$1</span>');
  h = h.replace(/(\d{1,3}(?:,\d{3})*\+)/g, '<span class="text-[var(--color-accent)] font-semibold">$1</span>');
  const keywords = ['PyTorch', 'Python', 'Power BI', 'Flask', 'SocketIO', 'NLP', 'ML', 'AI', 'VBA', 'Streamlit', 'Monte Carlo', 'TF-IDF', 'TextRank'];
  keywords.forEach(kw => {
    const regex = new RegExp(`\\b(${kw})\\b`, 'g');
    h = h.replace(regex, '<span class="text-[var(--color-text)] font-medium">$1</span>');
  });
  return h;
}
