import React from 'react';

interface ChartLegendProps {
  items: string[];
  colorMap: Record<string, string | undefined>;
  hiddenSet: Set<string>;
  onToggle: (key: string) => void;
}

export default function ChartLegend({ items, colorMap, hiddenSet, onToggle }: ChartLegendProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 pt-3">
      {items.map((item) => (
        <button
          key={item}
          type="button"
          className="flex max-w-full items-start gap-1.5 text-sm leading-tight text-left cursor-pointer rounded px-1 py-1 hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-pressed={!hiddenSet.has(item)}
          aria-label={`${hiddenSet.has(item) ? 'Show' : 'Hide'} ${item}`}
          style={{ opacity: hiddenSet.has(item) ? 0.4 : 1 }}
          onClick={() => onToggle(item)}
        >
          <div
            className="h-2 w-2 shrink-0 rounded-[2px]"
            style={{ backgroundColor: colorMap[item] }}
          />
          <span className="break-words">{item}</span>
        </button>
      ))}
    </div>
  );
}
