import type { SkillCategory } from '../types/index';

export const skillCategories: SkillCategory[] = [
  {
    name: 'Programming',
    skills: [
      { name: 'Python', proficiency: 90, icon: 'fa-brands fa-python' },
      { name: 'VBA', proficiency: 80, icon: 'fa-solid fa-file-code' },
      { name: 'PyQt5', proficiency: 75, icon: 'fa-solid fa-window-maximize' },
      { name: 'Selenium', proficiency: 85, icon: 'fa-solid fa-globe' },
    ],
  },
  {
    name: 'Analytics',
    skills: [
      { name: 'Excel Dashboards', proficiency: 90, icon: 'fa-solid fa-table' },
      { name: 'Power BI', proficiency: 80, icon: 'fa-solid fa-chart-pie' },
      { name: 'Google Analytics', proficiency: 70, icon: 'fa-solid fa-chart-simple' },
      { name: 'ArcGIS', proficiency: 65, icon: 'fa-solid fa-map-location-dot' },
    ],
  },
  {
    name: 'AI/ML',
    skills: [
      { name: 'spaCy', proficiency: 80, icon: 'fa-solid fa-brain' },
      { name: 'Gen AI Tools', proficiency: 85, icon: 'fa-solid fa-wand-magic-sparkles' },
      { name: 'Machine Learning', proficiency: 75, icon: 'fa-solid fa-microchip' },
      { name: 'NLP', proficiency: 80, icon: 'fa-solid fa-language' },
    ],
  },
  {
    name: 'Energy Domain',
    skills: [
      { name: 'Upstream Oil & Gas', proficiency: 90, icon: 'fa-solid fa-oil-well' },
      { name: 'Market Research', proficiency: 85, icon: 'fa-solid fa-magnifying-glass-chart' },
      { name: 'Subsea Analysis', proficiency: 80, icon: 'fa-solid fa-water' },
      { name: 'Contract Intelligence', proficiency: 75, icon: 'fa-solid fa-file-contract' },
    ],
  },
];
