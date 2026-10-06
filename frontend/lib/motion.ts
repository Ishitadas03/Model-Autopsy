import { Variants, Transition } from 'framer-motion';

export const EASING_EXPO_OUT = [0.22, 1, 0.36, 1] as const;

export const DURATIONS = {
  fast: 0.2,
  base: 0.45,
  slow: 0.9,
  stagger: 0.08,
} as const;

export const transitionFast: Transition = {
  duration: DURATIONS.fast,
  ease: EASING_EXPO_OUT,
};

export const transitionBase: Transition = {
  duration: DURATIONS.base,
  ease: EASING_EXPO_OUT,
};

export const transitionSlow: Transition = {
  duration: DURATIONS.slow,
  ease: EASING_EXPO_OUT,
};

export const fadeUp: Variants = {
  hidden: {
    opacity: 0,
    y: 20,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: transitionBase,
  },
};

export const fadeIn: Variants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: transitionBase,
  },
};

export const scaleIn: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: transitionBase,
  },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: DURATIONS.stagger,
    },
  },
};
