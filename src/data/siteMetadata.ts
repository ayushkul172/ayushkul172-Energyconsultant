import type { SiteMetadata } from '../types';

/**
 * Site-wide SEO metadata matching the content from index.html.
 * Used to inject JSON-LD, Open Graph, Twitter Card, canonical URL,
 * and robots meta into the rendered HTML at build time.
 *
 * Validates: Requirements 12.5
 */
export const siteMetadata: SiteMetadata = {
  title:
    'Ayush Kulshrestha - Energy Data Analyst & AI Consultant | Upstream Oil & Gas Expert',
  description:
    'Ayush Kulshrestha is a leading Energy Data Analyst and AI Consultant specializing in upstream oil & gas intelligence, automation tools, and strategic consulting. 90% efficiency gains through AI-powered solutions at Wood Mackenzie and KPMG.',
  canonicalUrl: 'https://www.akenergyconsultant.org/',
  ogImage:
    'https://images.unsplash.com/photo-1533134486753-c833f0ed4866?q=80&w=1200&h=630&fit=crop',
  jsonLd: {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: 'Ayush Kulshrestha',
    alternateName: 'AK Energy Consultant',
    jobTitle: 'Energy Data Analyst & AI Consultant',
    description:
      'Leading energy consultant specializing in AI-powered analytics for upstream oil & gas sector with 90%+ efficiency gains through intelligent automation solutions',
    url: 'https://www.akenergyconsultant.org/',
    image:
      'https://raw.githubusercontent.com/ayushkul172/Energyconsultant/main/Ayushprofile.png',
    sameAs: [
      'https://www.linkedin.com/in/ayush-k-5641461b2/',
      'https://www.akenergyconsultant.org/services',
    ],
    email: 'ayushkul404@yahoo.com',
    telephone: '+91-8851222155',
    address: {
      '@type': 'PostalAddress',
      addressLocality: 'Gurugram',
      addressRegion: 'Haryana',
      addressCountry: 'IN',
    },
    worksFor: {
      '@type': 'Organization',
      name: 'Wood Mackenzie',
    },
    alumniOf: [
      {
        '@type': 'CollegeOrUniversity',
        name: 'Galgotias College of Engineering & Technology',
      },
      {
        '@type': 'CollegeOrUniversity',
        name: 'Maharshi Dayanand University',
      },
    ],
    knowsAbout: [
      'Energy Data Analysis',
      'Artificial Intelligence',
      'Machine Learning',
      'Upstream Oil & Gas',
      'Python Programming',
      'Power BI',
      'Process Automation',
      'Strategic Consulting',
    ],
  },
  twitterCard: {
    'twitter:card': 'summary_large_image',
    'twitter:url': 'https://www.akenergyconsultant.org/',
    'twitter:title': 'Ayush Kulshrestha | Energy Data & Strategy',
    'twitter:description':
      'A modern, interactive portfolio website for Ayush Kulshrestha, showcasing expertise in energy data analysis, automation, and strategic consulting.',
    'twitter:image':
      'https://images.unsplash.com/photo-1533134486753-c833f0ed4866?q=80&w=1200&h=630&fit=crop',
  },
};

/**
 * Open Graph metadata fields used to populate <meta property="og:*"> tags.
 */
export const ogMetadata: Record<string, string> = {
  'og:type': 'website',
  'og:url': siteMetadata.canonicalUrl,
  'og:title': 'Ayush Kulshrestha | Energy Data & Strategy',
  'og:description':
    'A modern, interactive portfolio website for Ayush Kulshrestha, showcasing expertise in energy data analysis, automation, and strategic consulting.',
  'og:image': siteMetadata.ogImage,
};

/**
 * Robots meta content for search engine directives.
 */
export const robotsMeta = 'index, follow';
