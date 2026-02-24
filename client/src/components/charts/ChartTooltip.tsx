import React from 'react';
import type { TooltipProps } from 'recharts';
import { CurrencyFormatter } from '@/utils/formatters';

/**
 * Custom tooltip that filters zero-value items, formats values as currency,
 * and shows a total row at the bottom.
 */
export function SpendingTooltipContent({ active, payload, label, showTotal = true }: TooltipProps<number, string> & { showTotal?: boolean }) {
  if (!active || !payload?.length) return null;

  const items = payload
    .filter(item => item.value !== 0 && item.value !== undefined)
    .sort((a, b) => String(a.name).localeCompare(String(b.name)));

  if (items.length === 0) return null;

  const total = items.reduce((sum, item) => sum + (Number(item.value) || 0), 0);

  return (
    <div className="border-border/50 bg-background min-w-[8rem] rounded-lg border px-2.5 py-1.5 text-xs shadow-xl">
      {label && <div className="font-medium mb-1.5">{label}</div>}
      <div className="grid gap-1.5">
        {items.map((item) => (
          <div key={item.dataKey} className="flex items-center gap-2">
            <div
              className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
              style={{ backgroundColor: item.color }}
            />
            <div className="flex flex-1 justify-between items-center gap-4">
              <span className="text-muted-foreground">{String(item.name)}</span>
              <span className="text-foreground font-mono font-medium tabular-nums">
                {CurrencyFormatter.format(Number(item.value))}
              </span>
            </div>
          </div>
        ))}
        {showTotal && items.length > 1 && (
          <>
            <div className="border-t border-border/50 my-0.5" />
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 shrink-0" />
              <div className="flex flex-1 justify-between items-center gap-4">
                <span className="font-medium">Total</span>
                <span className="text-foreground font-mono font-medium tabular-nums">
                  {CurrencyFormatter.format(total)}
                </span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
