'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export interface NavSection {
  id: string;
  label: string;
}

export const REPORT_SECTIONS: NavSection[] = [
  { id: 'summary', label: '1. Executive Overview' },
  { id: 'dataset', label: '2. Dataset Characteristics' },
  { id: 'model', label: '3. Model Architecture' },
  { id: 'baseline', label: '4. Clean Baseline Reference' },
  { id: 'stress-config', label: '5. Stress Configuration' },
  { id: 'robustness', label: '6. Robustness Results' },
  { id: 'failures', label: '7. Failure Analysis' },
  { id: 'boundary', label: '8. Failure Boundary' },
  { id: 'statistics', label: '9. Statistical Validation' },
  { id: 'visualizations', label: '10. Visualizations' },
  { id: 'limitations', label: '11. Limitations & Caveats' },
  { id: 'reproducibility', label: '12. Reproducibility Audit' },
];

export function ReportNav() {
  const [activeSection, setActiveSection] = useState(REPORT_SECTIONS[0].id);

  // Scroll-spy observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { threshold: 0.3 }
    );

    REPORT_SECTIONS.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <nav className="sticky top-24 space-y-1 p-3 rounded-xl bg-surface border border-border shadow-xl text-xs select-none">
      <span className="text-[10px] font-cabin uppercase text-text-subtle px-3 py-1.5 block tracking-wider">
        Table of Contents
      </span>

      {REPORT_SECTIONS.map((sec) => {
        const isActive = activeSection === sec.id;

        return (
          <button
            key={sec.id}
            type="button"
            onClick={() => scrollTo(sec.id)}
            className={`relative w-full text-left px-3 py-2 rounded-lg font-manrope font-medium transition-colors flex items-center ${
              isActive
                ? 'bg-surface-2 text-white'
                : 'text-text-subtle hover:text-white hover:bg-white/5'
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="reportNavIndicator"
                className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-white rounded-r"
                transition={{ type: 'spring', stiffness: 500, damping: 35 }}
              />
            )}
            <span className="truncate">{sec.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
