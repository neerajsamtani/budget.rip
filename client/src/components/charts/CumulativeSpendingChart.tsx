import { ChartContainer, ChartTooltip } from '@/components/ui/chart';
import { SpendingTooltipContent } from './ChartTooltip';
import { MonthlyBreakdownData } from '@/hooks/useApi';
import { chartColorSequence } from '@/lib/chart-colors';
import React, { useMemo } from 'react';
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts';
import { getAvailableYears, getMonth, getYear, useHiddenSet } from './chart-utils';
import ChartLegend from './ChartLegend';
import type { ChartConfig } from '@/components/ui/chart';

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

interface Props {
  data: MonthlyBreakdownData;
}

export default function CumulativeSpendingChart({ data }: Props) {
  const [hiddenYears, toggleYear] = useHiddenSet();

  const { rows, years, chartConfig } = useMemo(() => {
    const availableYears = getAvailableYears(data);

    // Sum all categories per month, then compute running total per year
    const monthlyTotals: Record<string, Record<number, number>> = {};
    for (const year of availableYears) {
      monthlyTotals[year] = {};
    }

    for (const entries of Object.values(data)) {
      if (!Array.isArray(entries)) continue;
      for (const { date, amount } of entries) {
        const year = getYear(date);
        const month = getMonth(date);
        monthlyTotals[year][month] = (monthlyTotals[year][month] || 0) + amount;
      }
    }

    // Build rows: one per month (1-12), with cumulative totals per year.
    // Only include a data point if that month actually has data in the source.
    const chartRows: Record<string, unknown>[] = [];
    for (let m = 1; m <= 12; m++) {
      const row: Record<string, unknown> = { month: MONTH_LABELS[m - 1] };
      for (const year of availableYears) {
        const maxMonth = Math.max(0, ...Object.keys(monthlyTotals[year]).map(Number));
        if (m > maxMonth) continue;
        let cumulative = 0;
        for (let pm = 1; pm <= m; pm++) {
          cumulative += monthlyTotals[year][pm] || 0;
        }
        row[year] = cumulative;
      }
      chartRows.push(row);
    }

    const config: ChartConfig = {};
    availableYears.forEach((year, i) => {
      config[year] = {
        label: year,
        color: chartColorSequence[i % chartColorSequence.length],
      };
    });

    return { rows: chartRows, years: availableYears, chartConfig: config };
  }, [data]);

  const currentYear = String(new Date().getFullYear());
  const colorMap = Object.fromEntries(years.map(y => [y, chartConfig[y]?.color]));

  return (
    <div>
      <ChartContainer config={chartConfig} className="aspect-auto h-[350px] md:h-[450px] w-full">
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={8} />
          <YAxis tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
          <ChartTooltip content={<SpendingTooltipContent showTotal={false} />} />
          {years.map((year) => (
            <Line
              key={year}
              type="monotone"
              dataKey={year}
              stroke={chartConfig[year]?.color}
              strokeWidth={year === currentYear ? 3 : 1.5}
              strokeDasharray={year === currentYear ? undefined : '5 5'}
              dot={false}
              hide={hiddenYears.has(year)}
              connectNulls
            />
          ))}
        </LineChart>
      </ChartContainer>
      <ChartLegend items={years} colorMap={colorMap} hiddenSet={hiddenYears} onToggle={toggleYear} />
    </div>
  );
}
