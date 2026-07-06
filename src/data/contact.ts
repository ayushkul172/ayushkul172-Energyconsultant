import type { ContactMethod } from '../types/index';

export const contactMethods: ContactMethod[] = [
  {
    type: 'email',
    label: 'Email',
    value: 'ayushkul404@yahoo.com',
    href: 'mailto:ayushkul404@yahoo.com',
    icon: 'fa-solid fa-envelope',
    accentColor: 'from-cyan-500 to-blue-600',
  },
  {
    type: 'phone',
    label: 'Phone',
    value: '+91-8851222155',
    href: 'tel:+918851222155',
    icon: 'fa-solid fa-phone',
    accentColor: 'from-green-500 to-teal-600',
  },
  {
    type: 'linkedin',
    label: 'LinkedIn',
    value: 'linkedin.com/in/ayush-k-5641461b2',
    href: 'https://www.linkedin.com/in/ayush-k-5641461b2/',
    icon: 'fa-brands fa-linkedin',
    accentColor: 'from-blue-600 to-indigo-600',
  },
 {
    type: 'website',
    label: 'Download CV',
    value: 'Ayush Kulshrestha - CV.pdf',
    href: 'https://raw.githubusercontent.com/ayushkul172/ayushkul172-Energyconsultant/main/Ayush%20Kulshrestha%20-%20CV.pdf',
    icon: 'fa-solid fa-file-arrow-down',
    accentColor: 'from-orange-500 to-red-500',
  },

];
