'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface TabItem {
  id: string;
  label: string;
  count?: number;
}

interface TabsProps {
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
  layoutId?: string;
}

export function Tabs({
  tabs,
  activeId,
  onChange,
  className = '',
  layoutId = 'activeTab',
}: TabsProps) {
  return (
    <div
      role="tablist"
      className={`flex items-center gap-1 border-b border-white/10 ${className}`}
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={`relative px-4 py-2.5 text-sm font-manrope font-medium transition-colors select-none ${
              isActive ? 'text-white' : 'text-text-muted hover:text-white'
            }`}
          >
            <span className="flex items-center gap-2">
              {tab.label}
              {tab.count !== undefined && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full tabular-nums ${
                    isActive
                      ? 'bg-white/20 text-white'
                      : 'bg-white/5 text-text-subtle'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </span>

            {isActive && (
              <motion.div
                layoutId={layoutId}
                className="absolute bottom-0 left-0 right-0 h-[2px] bg-white shadow-[0_0_8px_rgba(255,255,255,0.4)]"
                transition={{ type: 'spring', stiffness: 500, damping: 35 }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
