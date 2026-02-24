import { Spinner } from "@/components/ui/spinner";
import { DateTime } from "luxon";
import React, { useEffect, useMemo, useRef, useState } from "react";
import CumulativeSpendingChart from "../components/charts/CumulativeSpendingChart";
import { filterByCategories, filterByYear, filterToSpending } from "../components/charts/chart-utils";
import StackedSpendingChart from "../components/charts/StackedSpendingChart";
import TopEventsChart from "../components/charts/TopEventsChart";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import YearFilter, { type Year } from "../components/YearFilter";
import { useCategories, useEvents, useMonthlyBreakdown } from "../hooks/useApi";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Label } from "../components/ui/label";
import MultiSelectFilter from "../components/MultiSelectFilter";

const TOP_N_OPTIONS = ['5', '10', '20'] as const;

export default function GraphsPage() {
  const [year, setYear] = useState<Year>(() => String(DateTime.utc().year) as Year);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [topN, setTopN] = useState<string>('10');

  const { data: breakdownData = {}, isLoading: isLoadingBreakdown, error: breakdownError } = useMonthlyBreakdown();
  const { data: categories = [] } = useCategories();

  // Initialize selectedCategories once categories load — exclude Income and Investment by default
  const categoriesInitialized = useRef(false);
  useEffect(() => {
    if (categories.length > 0 && !categoriesInitialized.current) {
      categoriesInitialized.current = true;
      const EXCLUDED_BY_DEFAULT = new Set(['Income', 'Investment']);
      setSelectedCategories(categories.map(c => c.name).filter(n => !EXCLUDED_BY_DEFAULT.has(n)));
    }
  }, [categories]);

  // Compute time range for events from selected year
  const { startTime, endTime } = useMemo(() => {
    const start = DateTime.fromFormat(year, "yyyy", { zone: 'utc' });
    return {
      startTime: start.toUnixInteger(),
      endTime: start.endOf("year").toUnixInteger(),
    };
  }, [year]);

  const { data: events = [], isLoading: isLoadingEvents } = useEvents(startTime, endTime);

  // Shared category-filtered breakdown data
  const categoryFilteredData = useMemo(
    () => filterByCategories(breakdownData, selectedCategories),
    [breakdownData, selectedCategories]
  );

  const stackedData = useMemo(
    () => filterByYear(categoryFilteredData, year),
    [categoryFilteredData, year]
  );

  const cumulativeData = useMemo(
    () => filterByCategories(filterToSpending(breakdownData), selectedCategories),
    [breakdownData, selectedCategories]
  );

  if (breakdownError) {
    return (
      <PageContainer>
        <PageHeader>
          <H1>Graphs</H1>
        </PageHeader>
        <div className="flex items-center justify-center h-64">
          <Body className="text-destructive">Error loading data. Please try again.</Body>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader>
        <H1>Graphs</H1>
        <Body className="text-muted-foreground">
          Visual analysis of your spending patterns and financial trends
        </Body>
      </PageHeader>

      {isLoadingBreakdown ? (
        <div className="flex items-center justify-center h-64">
          <Spinner size="md" className="text-muted-foreground" />
        </div>
      ) : (
        <div className="space-y-8">
          {/* Shared filters */}
          <div className="flex flex-wrap items-end gap-3">
            <YearFilter year={year} setYear={setYear} />
            <MultiSelectFilter
              label="Category"
              options={categories}
              selected={selectedCategories}
              onChange={setSelectedCategories}
            />
          </div>

          {/* Stacked Spending */}
          <div className="bg-white rounded-xl border p-4 md:p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Monthly Spending by Category</h2>
            <StackedSpendingChart data={stackedData} />
          </div>

          {/* Cumulative Spending (all years) */}
          <div className="bg-white rounded-xl border p-4 md:p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Cumulative Spending (Year over Year)</h2>
            <CumulativeSpendingChart data={cumulativeData} />
          </div>

          {/* Top Events */}
          <div className="bg-white rounded-xl border p-4 md:p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Top Events ({year})</h2>

            <div className="flex flex-wrap items-end gap-4 mb-4">
              {/* Top N selector */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Show Top</Label>
                <Select value={topN} onValueChange={setTopN}>
                  <SelectTrigger className="w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white border">
                    {TOP_N_OPTIONS.map(n => (
                      <SelectItem key={n} value={n}>{n}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {isLoadingEvents ? (
              <div className="flex items-center justify-center h-48">
                <Spinner size="md" className="text-muted-foreground" />
              </div>
            ) : (
              <TopEventsChart
                events={events}
                selectedCategories={selectedCategories}
                topN={parseInt(topN)}
              />
            )}
          </div>
        </div>
      )}
    </PageContainer>
  );
}
