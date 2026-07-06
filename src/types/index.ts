// Shared TypeScript interfaces for the Animated Portfolio Revamp

export interface Service {
  icon: string;           // Font Awesome class
  title: string;
  description: string;
  pricing: string;
  features: string[];
  accentColor?: string;   // gradient color for hover glow
}

export interface SpotlightProject {
  title: string;
  situation: string;
  task: string;
  action: string;
  techStack: string[];
  image: string;
  results: ProjectResult[];
  accentColor: string;    // for card glow & overlay accent
}

export interface ProjectResult {
  metric: string;
  description: string;
}

export interface AdditionalProject {
  title: string;
  challenge: string;
  action: string;
  result: {
    text: string;
    highlight: string;
  };
}

export interface Experience {
  company: string;
  title: string;
  date: string;
  description: string;
  logo?: string;          // company logo URL
}

export interface SkillCategory {
  name: string;           // e.g., "Programming", "Analytics"
  skills: Skill[];
}

export interface Skill {
  name: string;
  proficiency: number;    // 0–100 integer
  icon?: string;
}

export interface Certification {
  icon: string;
  title: string;
  issuer: string;
}

export interface ContactMethod {
  type: 'email' | 'phone' | 'linkedin' | 'website';
  label: string;
  value: string;
  href: string;
  icon: string;
  accentColor: string;
}

export interface SiteMetadata {
  title: string;
  description: string;
  canonicalUrl: string;
  ogImage: string;
  jsonLd: Record<string, unknown>;
  twitterCard: Record<string, string>;
}

export interface NavItem {
  id: string;
  label: string;
  sectionIndex: number;
}

export interface ThemeConfig {
  mode: 'dark' | 'light';
  colors: {
    background: string;
    cardSurface: string;
    accent: string;
    accentSecondary: string;
    text: string;
    textSubtle: string;
  };
}
