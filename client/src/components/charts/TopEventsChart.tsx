import { ChartContainer, ChartTooltip } from '@/components/ui/chart';
import { SpendingTooltipContent } from './ChartTooltip';
import { EventInterface } from '@/components/Event';
import { chartColorSequence } from '@/lib/chart-colors';
import React, { useMemo } from 'react';
import { Bar, BarChart, XAxis, YAxis, Cell } from 'recharts';
import type { ChartConfig } from '@/components/ui/chart';

interface Props {
  events: EventInterface[];
  selectedCategories: string[];
  topN: number;
}

export default function TopEventsChart({ events, selectedCategories, topN }: Props) {
  const { rows, chartConfig, categoryColorMap } = useMemo(() => {
    const filtered = (selectedCategories.length === 0
      ? events
      : events.filter(e => selectedCategories.includes(e.category)))
      .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount))
      .slice(0, topN);

    // Build a color map per unique category
    const uniqueCategories = Array.from(new Set(filtered.map(e => e.category)));
    const colorMap: Record<string, string> = {};
    uniqueCategories.forEach((cat, i) => {
      colorMap[cat] = chartColorSequence[i % chartColorSequence.length];
    });

    const config: ChartConfig = {
      amount: { label: 'Amount' },
    };
    uniqueCategories.forEach((cat) => {
      config[cat] = { label: cat, color: colorMap[cat] };
    });

    const chartRows = filtered.map(e => ({
      name: e.name,
      amount: Math.abs(e.amount),
      category: e.category,
    }));

    return { rows: chartRows, chartConfig: config, categoryColorMap: colorMap };
  }, [events, selectedCategories, topN]);

  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-8">No events to display.</p>;
  }

  return (
    <ChartContainer config={chartConfig} className="aspect-auto w-full" style={{ height: Math.max(200, rows.length * 40) }}>
      <BarChart data={rows} layout="vertical" margin={{ left: 20 }}>
        <XAxis type="number" tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
        <YAxis type="category" dataKey="name" tickLine={false} axisLine={false} width={150} tick={{ fontSize: 12 }} />
        <ChartTooltip content={<SpendingTooltipContent />} />
        <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
          {rows.map((row) => (
            <Cell key={row.name} fill={categoryColorMap[row.category]} />
          ))}
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}
