import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ children, className = '', hoverEffect = false, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`bg-[#0a0c16]/80 backdrop-blur-xl border border-white/12 rounded-2xl shadow-[0_12px_32px_rgba(0,0,0,0.6)] transition-all duration-300 ${
          hoverEffect
            ? 'hover:border-sky-400/40 hover:bg-[#0e1222] hover:shadow-[0_16px_40px_rgba(56,189,248,0.12)] hover:-translate-y-1'
            : ''
        } ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
