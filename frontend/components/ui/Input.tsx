import React from 'react';
import { Search, X } from 'lucide-react';

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', error, label, id, ...props }, ref) => {
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
        <input
          id={id}
          ref={ref}
          className={`w-full bg-surface-2 border border-border rounded-[8px] px-3 py-2 text-sm text-white placeholder:text-text-subtle transition-all duration-200 hover:border-border-strong disabled:opacity-50 disabled:pointer-events-none ${
            error ? 'border-accent focus-visible:ring-accent' : ''
          } ${className}`}
          {...props}
        />
        {error && (
          <p className="text-xs text-accent font-medium mt-1">{error}</p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

export interface SearchInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
}

export const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  ({ className = '', value, onClear, onChange, ...props }, ref) => {
    return (
      <div className="relative w-full">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle pointer-events-none"
          aria-hidden="true"
        >
          <title>Search</title>
        </Search>
        <input
          ref={ref}
          type="text"
          value={value}
          onChange={onChange}
          className={`w-full bg-surface-2 border border-border rounded-[8px] pl-9 pr-8 py-2 text-sm text-white placeholder:text-text-subtle transition-all duration-200 hover:border-border-strong ${className}`}
          placeholder="Search..."
          {...props}
        />
        {value && onClear && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-text-subtle hover:text-white transition-colors"
            aria-label="Clear search"
          >
            <X className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        )}
      </div>
    );
  }
);
SearchInput.displayName = 'SearchInput';
