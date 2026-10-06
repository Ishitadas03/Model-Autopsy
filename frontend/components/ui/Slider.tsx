import React from 'react';

export interface SliderProps {
  value: number;
  onChange: (val: number) => void;
  min: number;
  max: number;
  step?: number;
  label?: string;
  unit?: string;
  formatValue?: (val: number) => string;
  disabled?: boolean;
  className?: string;
}

export function Slider({
  value,
  onChange,
  min,
  max,
  step = 1,
  label,
  unit = '',
  formatValue,
  disabled = false,
  className = '',
}: SliderProps) {
  const percentage = ((value - min) / (max - min)) * 100;
  const displayVal = formatValue ? formatValue(value) : `${value}${unit}`;

  return (
    <div className={`w-full space-y-2 ${className}`}>
      <div className="flex items-center justify-between text-xs">
        {label && (
          <span className="font-cabin font-medium text-text-muted">{label}</span>
        )}
        <span className="font-manrope font-semibold text-white tabular-nums">
          {displayVal}
        </span>
      </div>

      <div className="relative flex items-center">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="w-full h-1.5 bg-surface-2 rounded-lg appearance-none cursor-pointer accent-white focus-visible:outline-none"
          style={{
            background: `linear-gradient(to right, white ${percentage}%, #131318 ${percentage}%)`,
          }}
        />
      </div>
    </div>
  );
}
