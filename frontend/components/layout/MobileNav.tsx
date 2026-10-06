'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus } from 'lucide-react';
import { Logo } from '../ui/Logo';
import { CommandStatus } from './CommandStatus';

interface MobileNavProps {
  open: boolean;
  onClose: () => void;
  links: { label: string; href: string }[];
  currentPath: string;
}

export function MobileNav({
  open,
  onClose,
  links,
  currentPath,
}: MobileNavProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm"
          />

          {/* Drawer content */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="relative h-full w-[280px] bg-surface border-r border-border p-6 flex flex-col justify-between z-10"
          >
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-white/5">
                <Logo size="sm" />
                <button
                  type="button"
                  onClick={onClose}
                  className="p-1 rounded-md text-text-subtle hover:text-white"
                  aria-label="Close menu"
                >
                  <X className="w-5 h-5" aria-hidden="true" />
                </button>
              </div>

              <Link
                href="/workspace"
                onClick={onClose}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-[10px] bg-white text-black font-cabin font-medium text-xs shadow-sm hover:bg-[#e8e8e8]"
              >
                <Plus className="w-3.5 h-3.5" aria-hidden="true" />
                <span>New Autopsy</span>
              </Link>

              <nav className="flex flex-col gap-2">
                {links.map((link) => {
                  const isActive = currentPath.startsWith(link.href);
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={onClose}
                      className={`px-3 py-2 rounded-md text-sm font-manrope font-medium transition-colors ${
                        isActive
                          ? 'bg-surface-2 text-white font-semibold'
                          : 'text-text-muted hover:text-white hover:bg-white/5'
                      }`}
                    >
                      {link.label}
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="pt-4 border-t border-white/5 flex flex-col gap-3">
              <CommandStatus />
              <p className="text-[10px] text-text-subtle">
                Model Autopsy v0.1.0 • Research Edition
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
