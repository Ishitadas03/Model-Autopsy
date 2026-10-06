'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { EASING_EXPO_OUT } from '@/lib/motion';

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: EASING_EXPO_OUT }}
      className="w-full flex-1 flex flex-col"
    >
      {children}
    </motion.div>
  );
}
