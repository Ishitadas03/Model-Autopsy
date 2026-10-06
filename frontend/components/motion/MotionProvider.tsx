'use client';

import React from 'react';
import { MotionConfig } from 'framer-motion';
import { ToastProvider } from '@/components/ui/Toast';

export function MotionProvider({ children }: { children: React.ReactNode }) {
  return (
    <MotionConfig reducedMotion="user">
      <ToastProvider>
        {children}
      </ToastProvider>
    </MotionConfig>
  );
}
