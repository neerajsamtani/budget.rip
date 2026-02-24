import { ChartConfig } from '@/components/ui/chart';
import { MonthlyBreakdownData } from '@/hooks/useApi';
import { chartColorSequence } from '@/lib/chart-colors';
import { useCallback, useState } from 'react';

export const MONTH_ABBREVS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Converts "1-2023" → "Jan '23" */
export function formatMonthYear(dateStr: string): string {
  const [month, year] = dateStr.split('-');
  return `${MONTH_ABBREVS[parseInt(month) - 1]} '${year.slice(2)}`;
}

/** Extracts the year from "1-2023" → "2023" */
export function getYear(dateStr: string): string {
  return dateStr.split('-')[1];
}

/** Extracts the month number from "1-2023" → 1 */
export function getMonth(dateStr: string): number {
  return parseInt(dateStr.split('-')[0]);
}

/**
 * Transforms MonthlyBreakdownData into recharts row-per-date format.
 * Input:  { "Dining": [{date: "1-2023", amount: 100}], "Shopping": [{date: "1-2023", amount: 200}] }
 * Output: [{ date: "1-2023", formattedDate: "Jan '23", Dining: 100, Shopping: 200 }]
 */
export function toRowPerDate(data: MonthlyBreakdownData): Record<string, unknown>[] {
  const dateMap: Record<string, Record<string, unknown>> = {};

  for (const [category, entries] of Object.entries(data)) {
    if (!Array.isArray(entries)) continue;
    for (const { date, amount } of entries) {
      if (!dateMap[date]) {
        dateMap[date] = { date, formattedDate: formatMonthYear(date) };
      }
      dateMap[date][category] = amount;
    }
  }

  // Sort by date chronologically
  return Object.values(dateMap).sort((a, b) => {
    const [mA, yA] = (a.date as string).split('-').map(Number);
    const [mB, yB] = (b.date as string).split('-').map(Number);
    return yA !== yB ? yA - yB : mA - mB;
  });
}

/** Builds a ChartConfig mapping category names to colors from chartColorSequence */
export function buildChartConfig(categories: string[]): ChartConfig {
  const config: ChartConfig = {};
  categories.forEach((cat, i) => {
    config[cat] = {
      label: cat,
      color: chartColorSequence[i % chartColorSequence.length],
    };
  });
  return config;
}

/** Filters MonthlyBreakdownData to only include entries for a specific year */
export function filterByYear(data: MonthlyBreakdownData, year: string): MonthlyBreakdownData {
  const filtered: MonthlyBreakdownData = {};
  for (const [category, entries] of Object.entries(data)) {
    if (!Array.isArray(entries)) continue;
    const yearEntries = entries.filter(e => getYear(e.date) === year);
    if (yearEntries.length > 0) {
      filtered[category] = yearEntries;
    }
  }
  return filtered;
}

// Categories excluded from spending charts — also used by EventsPage.calculateSpending
export const NON_SPENDING_CATEGORIES = ['Income', 'Investment'];

/** Filters MonthlyBreakdownData to only include the specified categories.
 *  If categories is empty, returns data unmodified. */
export function filterByCategories(data: MonthlyBreakdownData, categories: string[]): MonthlyBreakdownData {
  if (categories.length === 0) return data;
  const allowed = new Set(categories);
  const filtered: MonthlyBreakdownData = {};
  for (const [cat, entries] of Object.entries(data)) {
    if (allowed.has(cat)) filtered[cat] = entries;
  }
  return filtered;
}

/** Returns sorted unique years found in the data */
export function getAvailableYears(data: MonthlyBreakdownData): string[] {
  const years = new Set<string>();
  for (const entries of Object.values(data)) {
    if (!Array.isArray(entries)) continue;
    for (const { date } of entries) {
      years.add(getYear(date));
    }
  }
  return Array.from(years).sort();
}

/** Hook for managing a set of hidden items (categories, years, etc.) in chart legends */
export function useHiddenSet(): [Set<string>, (key: string) => void] {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const toggle = useCallback((key: string) => {
    setHidden(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);
  return [hidden, toggle];
}
