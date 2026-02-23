import { ChartContainer, ChartTooltip } from '@/components/ui/chart';
import { SpendingTooltipContent } from './ChartTooltip';
import { MonthlyBreakdownData } from '@/hooks/useApi';
import React, { useMemo } from 'react';
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts';
import { buildChartConfig, toRowPerDate, useHiddenSet } from './chart-utils';
import ChartLegend from './ChartLegend';

interface Props {
  data: MonthlyBreakdownData;
}

export default function StackedSpendingChart({ data }: Props) {
  const [hiddenCategories, toggleCategory] = useHiddenSet();
  const categories = Object.keys(data).filter(k => Array.isArray(data[k]));
  const chartConfig = buildChartConfig(categories);
  const rows = toRowPerDate(data);

  // Determine sign of each category so positive and negative stack independently
  const categorySign = useMemo(() => {
    const signs: Record<string, 'pos' | 'neg'> = {};
    for (const [cat, entries] of Object.entries(data)) {
      if (!Array.isArray(entries)) continue;
      const total = entries.reduce((sum, e) => sum + e.amount, 0);
      signs[cat] = total < 0 ? 'neg' : 'pos';
    }
    return signs;
  }, [data]);

  const colorMap = Object.fromEntries(categories.map(cat => [cat, chartConfig[cat]?.color]));

  return (
    <div>
      <ChartContainer config={chartConfig} className="aspect-auto h-[350px] md:h-[450px] w-full">
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="formattedDate" tickLine={false} axisLine={false} tickMargin={8} />
          <YAxis tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
          <ChartTooltip content={<SpendingTooltipContent />} />
          {categories.map((cat) => (
            <Bar
              key={cat}
              dataKey={cat}
              stackId={categorySign[cat] ?? 'pos'}
              fill={chartConfig[cat]?.color}
              hide={hiddenCategories.has(cat)}
            />
          ))}
        </BarChart>
      </ChartContainer>
      <ChartLegend items={categories} colorMap={colorMap} hiddenSet={hiddenCategories} onToggle={toggleCategory} />
    </div>
  );
}
