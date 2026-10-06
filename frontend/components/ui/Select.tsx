import React from 'react';
import { ChevronDown } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
  label?: string;
  error?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className = '', options, label, error, id, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={id}
            className="block text-xs font-cabin font-medium text-text-muted"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            id={id}
            ref={ref}
            className={`w-full appearance-none bg-surface-2 border border-border rounded-[8px] pl-3 pr-8 py-2 text-sm text-white transition-all duration-200 hover:border-border-strong disabled:opacity-50 disabled:pointer-events-none cursor-pointer ${
              error ? 'border-accent' : ''
            } ${className}`}
            {...props}
          >
            {options.map((opt) => (
              <option
                key={opt.value}
                value={opt.value}
                className="bg-surface text-white py-1"
              >
                {opt.label}
              </option>
            ))}
          </select>
          <ChevronDown
            className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle pointer-events-none"
            aria-hidden="true"
          />
        </div>
        {error && <p className="text-xs text-accent font-medium mt-1">{error}</p>}
      </div>
    );
  }
);
Select.displayName = 'Select';
