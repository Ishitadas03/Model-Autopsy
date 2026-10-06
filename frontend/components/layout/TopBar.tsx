'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bell, Menu, X } from 'lucide-react';
import { Logo } from '../ui/Logo';
import { CommandStatus } from './CommandStatus';
import { MobileNav } from './MobileNav';

export const NAV_LINKS = [
  { label: 'Experiments', href: '/experiments' },
  { label: 'Datasets', href: '/datasets' },
  { label: 'Models', href: '/models' },
  { label: 'Stress Tests', href: '/stress-tests' },
  { label: 'Reports', href: '/reports' },
];

export function TopBar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-bg/90 backdrop-blur-md">
        <div className="max-w-[1440px] mx-auto h-16 px-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-8">
            <Logo size="md" />

            {/* Desktop Navigation Links */}
            <nav className="hidden lg:flex items-center gap-6">
              {NAV_LINKS.map((link) => {
                const isActive = pathname.startsWith(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`relative py-1 text-xs font-manrope font-medium transition-colors ${
                      isActive
                        ? 'text-white'
                        : 'text-text-muted hover:text-white'
                    }`}
                  >
                    <span>{link.label}</span>
                    {isActive && (
                      <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-white rounded-full" />
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <CommandStatus className="hidden sm:inline-flex" />

            {/* Notifications Button */}
            <button
              type="button"
              className="p-2 rounded-md text-text-subtle hover:text-white hover:bg-white/5 transition-colors"
              aria-label="View notifications"
            >
              <Bell className="w-4 h-4" aria-hidden="true" />
            </button>

            {/* Square Avatar "U" */}
            <div
              className="w-8 h-8 rounded-[6px] bg-surface-2 border border-white/15 flex items-center justify-center font-manrope font-bold text-xs text-white select-none"
              title="Current User"
            >
              U
            </div>

            {/* Mobile Hamburger Toggle */}
            <button
              type="button"
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 rounded-md text-text-subtle hover:text-white hover:bg-white/5 transition-colors"
              aria-label="Toggle navigation menu"
            >
              {mobileOpen ? (
                <X className="w-5 h-5" aria-hidden="true" />
              ) : (
                <Menu className="w-5 h-5" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Slide-in Drawer */}
      <MobileNav
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        links={NAV_LINKS}
        currentPath={pathname}
      />
    </>
  );
}
