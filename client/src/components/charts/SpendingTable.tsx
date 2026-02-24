import { MonthlyBreakdownData } from '@/hooks/useApi';
import React, { useMemo } from 'react';
import { CurrencyFormatter } from '@/utils/formatters';
import { formatMonthYear, getMonth, getYear, getCategorySign } from './chart-utils';

interface Props {
  data: MonthlyBreakdownData;
  colorMap: Record<string, string>;
  onCellClick: (category: string, date: string) => void;
}

const CLICKABLE_CELL = 'px-3 py-2 text-right tabular-nums cursor-pointer hover:bg-muted';
const EMPTY_CELL = 'px-3 py-2 text-right tabular-nums text-muted-foreground';

export default function SpendingTable({ data, colorMap, onCellClick }: Props) {
  const categories = useMemo(
    () => Object.keys(data).filter(k => Array.isArray(data[k])),
    [data]
  );

  const categorySign = useMemo(() => getCategorySign(data), [data]);

  const months = useMemo(() => {
    const dateSet = new Set<string>();
    for (const entries of Object.values(data)) {
      if (!Array.isArray(entries)) continue;
      for (const { date } of entries) dateSet.add(date);
    }
    return Array.from(dateSet).sort((a, b) => {
      const ya = Number(getYear(a)), yb = Number(getYear(b));
      return ya !== yb ? ya - yb : getMonth(a) - getMonth(b);
    });
  }, [data]);

  const getCellValue = (category: string, date: string): number | null => {
    const entry = data[category]?.find(e => e.date === date);
    return entry?.amount ?? null;
  };

  const rowTotal = (category: string) =>
    months.reduce((sum, date) => sum + (getCellValue(category, date) ?? 0), 0);

  const colTotal = (date: string) =>
    categories.reduce((sum, cat) => sum + (getCellValue(cat, date) ?? 0), 0);

  const grandTotal = categories.reduce((sum, cat) => sum + rowTotal(cat), 0);

  return (
    <div className="-mx-4 -mb-4 md:-mx-6 md:-mb-6 overflow-auto mt-4 border-t">
      <table className="w-full text-sm">
        <thead className="bg-muted border-b">
          <tr>
            <th className="h-10 px-3 text-left font-medium text-foreground sticky left-0 bg-muted z-10">
              Category
            </th>
            {months.map(date => (
              <th key={date} className="h-10 px-3 text-right font-medium text-foreground whitespace-nowrap">
                {formatMonthYear(date)}
              </th>
            ))}
            <th className="h-10 px-3 text-right font-medium text-foreground">Total</th>
          </tr>
        </thead>
        <tbody className="[&_tr:last-child]:border-0">
          {categories.map((category) => {
            const color = colorMap[category] ?? '';
            const total = rowTotal(category);
            return (
              <tr key={category} className="border-b transition-colors hover:bg-gray-50">
                <td className="px-3 py-2 font-medium sticky left-0 bg-white z-10">
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-block size-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    {category}
                  </div>
                </td>
                {months.map(date => {
                  const val = getCellValue(category, date);
                  const hasValue = val !== null && val !== 0;
                  return (
                    <td
                      key={date}
                      className={hasValue ? CLICKABLE_CELL : EMPTY_CELL}
                      onClick={hasValue ? () => onCellClick(category, date) : undefined}
                    >
                      {hasValue ? <span className="underline">{CurrencyFormatter.format(categorySign[category] === 'neg' ? val! : Math.abs(val!))}</span> : '—'}
                    </td>
                  );
                })}
                <td
                  className={total !== 0 ? `${CLICKABLE_CELL} font-medium` : `${EMPTY_CELL} font-medium`}
                  onClick={total !== 0 ? () => onCellClick(category, 'all') : undefined}
                >
                  {total !== 0 ? <span className="underline">{CurrencyFormatter.format(categorySign[category] === 'neg' ? total : Math.abs(total))}</span> : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot className="bg-muted border-t font-medium">
          <tr>
            <td className="px-3 py-2 sticky left-0 bg-muted z-10">Total</td>
            {months.map(date => {
              const total = colTotal(date);
              return (
                <td
                  key={date}
                  className={total !== 0 ? CLICKABLE_CELL : EMPTY_CELL}
                  onClick={total !== 0 ? () => onCellClick('all', date) : undefined}
                >
                  {total !== 0 ? <span className="underline">{CurrencyFormatter.format(total)}</span> : '—'}
                </td>
              );
            })}
            <td
              className={`${CLICKABLE_CELL} font-medium`}
              onClick={() => onCellClick('all', 'all')}
            >
              <span className="underline">{CurrencyFormatter.format(grandTotal)}</span>
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
