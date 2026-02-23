import React from 'react';

interface ChartLegendProps {
  items: string[];
  colorMap: Record<string, string | undefined>;
  hiddenSet: Set<string>;
  onToggle: (key: string) => void;
}

export default function ChartLegend({ items, colorMap, hiddenSet, onToggle }: ChartLegendProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3 pt-3">
      {items.map((item) => (
        <button
          key={item}
          type="button"
          className="flex items-center gap-1.5 text-xs cursor-pointer"
          style={{ opacity: hiddenSet.has(item) ? 0.4 : 1 }}
          onClick={() => onToggle(item)}
        >
          <div
            className="h-2 w-2 shrink-0 rounded-[2px]"
            style={{ backgroundColor: colorMap[item] }}
          />
          {item}
        </button>
      ))}
    </div>
  );
}
