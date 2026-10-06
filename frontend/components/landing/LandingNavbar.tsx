'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, ArrowRight } from 'lucide-react';
import { Logo } from '../ui/Logo';

export function LandingNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [hoveredNav, setHoveredNav] = useState<string | null>(null);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 24);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [mobileMenuOpen]);

  const navLinks = [
    { label: 'Features', href: '#features' },
    { label: 'How it works', href: '#how-it-works' },
    { label: 'Stress Tests', href: '#stress-tests' },
    { label: 'Results', href: '#results' },
    { label: 'Docs', href: '/docs' },
  ];

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-30 transition-all duration-300 ${
          scrolled
            ? 'bg-black/60 backdrop-blur-md border-b border-white/8 py-3.5 shadow-lg'
            : 'bg-transparent py-5'
        }`}
      >
        <div className="max-w-[1440px] mx-auto px-6 md:px-12 xl:px-[120px] flex items-center justify-between">
          <div className="flex items-center gap-10">
            <Logo size="md" />

            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-7">
              {navLinks.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  onMouseEnter={() => setHoveredNav(item.label)}
                  onMouseLeave={() => setHoveredNav(null)}
                  className="relative text-sm font-manrope font-medium text-white transition-opacity hover:opacity-80 py-1"
                >
                  <span>{item.label}</span>
                  {hoveredNav === item.label && (
                    <motion.div
                      layoutId="navHoverUnderline"
                      className="absolute bottom-0 left-0 right-0 h-[1px] bg-white"
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      exit={{ scaleX: 0 }}
                      transition={{ duration: 0.2 }}
                    />
                  )}
                </Link>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {/* Desktop CTA */}
            <Link
              href="/workspace"
              className="hidden sm:inline-flex items-center gap-2 px-4 py-2 rounded-[8px] border border-white/30 text-sm font-manrope font-semibold text-white transition-all duration-200 hover:bg-white hover:text-black hover:border-white group"
            >
              <span>Run an Autopsy</span>
              <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
            </Link>

            {/* Mobile Hamburger */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 text-white hover:opacity-80 transition-opacity"
              aria-label="Open navigation menu"
            >
              <Menu className="w-6 h-6" />
            </button>
          </div>
        </div>
      </header>

      {/* Full-screen Mobile Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 z-50 bg-black flex flex-col justify-between p-6 md:hidden"
            role="dialog"
            aria-modal="true"
          >
            <div className="flex items-center justify-between pb-6 border-b border-white/10">
              <Logo size="md" />
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="p-2 text-white hover:opacity-80"
                aria-label="Close menu"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <nav className="flex flex-col gap-6 my-auto py-8">
              {navLinks.map((item, idx) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.08 * idx, duration: 0.3 }}
                >
                  <Link
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className="text-2xl font-manrope font-semibold text-white hover:text-accent transition-colors"
                  >
                    {item.label}
                  </Link>
                </motion.div>
              ))}
            </nav>

            <div className="space-y-4 pt-6 border-t border-white/10">
              <Link
                href="/workspace"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-[10px] bg-white text-black font-cabin font-semibold text-base shadow-sm hover:bg-[#e8e8e8]"
              >
                <span>Run an Autopsy</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="text-center text-xs text-text-subtle">
                AI Model Reliability Lab • Seeded Reproducible Runs
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
