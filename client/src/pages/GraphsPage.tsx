import { Spinner } from "@/components/ui/spinner";
import { Table2 } from "lucide-react";
import { DateTime } from "luxon";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { buildChartConfig, filterByCategories, filterByYear, getAvailableYears, NON_SPENDING_CATEGORIES } from "../components/charts/chart-utils";
import CumulativeSpendingChart from "../components/charts/CumulativeSpendingChart";
import SpendingDrillDown from "../components/charts/SpendingDrillDown";
import SpendingTable from "../components/charts/SpendingTable";
import StackedSpendingChart from "../components/charts/StackedSpendingChart";
import MultiSelectFilter from "../components/MultiSelectFilter";
import { Button } from "../components/ui/button";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import YearFilter from "../components/YearFilter";
import { useCategories, useEvents, useMonthlyBreakdown } from "../hooks/useApi";

export default function GraphsPage() {
  const [year, setYear] = useState<string>(() => String(DateTime.utc().year));
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');
  const [drillDown, setDrillDown] = useState<{ category: string; date: string } | null>(null);

  const { data: breakdownData = {}, isLoading: isLoadingBreakdown, error: breakdownError } = useMonthlyBreakdown();
  const availableYears = useMemo(() => getAvailableYears(breakdownData), [breakdownData]);
  const { data: categories = [] } = useCategories();

  // Initialize selectedCategories once categories load — exclude Income and Investment by default
  const categoriesInitialized = useRef(false);
  useEffect(() => {
    if (categories.length > 0 && !categoriesInitialized.current) {
      categoriesInitialized.current = true;
      setSelectedCategories(categories.map(c => c.name).filter(n => !NON_SPENDING_CATEGORIES.includes(n)));
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

  const { data: allEvents = [] } = useEvents(startTime, endTime);
  const events = useMemo(
    () => allEvents.filter(e => selectedCategories.includes(e.category)),
    [allEvents, selectedCategories]
  );

  // Shared category-filtered breakdown data
  const categoryFilteredData = useMemo(
    () => filterByCategories(breakdownData, selectedCategories),
    [breakdownData, selectedCategories]
  );

  const stackedData = useMemo(
    () => filterByYear(categoryFilteredData, year),
    [categoryFilteredData, year]
  );

  const chartConfig = useMemo(
    () => buildChartConfig(Object.keys(stackedData).filter(k => Array.isArray(stackedData[k]))),
    [stackedData]
  );
  const colorMap = useMemo(
    () => Object.fromEntries(Object.keys(chartConfig).map(cat => [cat, chartConfig[cat]?.color ?? ''])),
    [chartConfig]
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
            <YearFilter years={availableYears} year={year} setYear={setYear} />
            <MultiSelectFilter
              label="Category"
              options={categories}
              selected={selectedCategories}
              onChange={setSelectedCategories}
            />
          </div>

          {/* Stacked Spending */}
          <div className="bg-white rounded-xl border p-4 md:p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Monthly Spending by Category</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewMode(viewMode === 'table' ? 'chart' : 'table')}
              >
                <Table2 className="size-4" />
                {viewMode === 'table' ? 'Hide table' : 'Show table'}
              </Button>
            </div>
            <StackedSpendingChart data={stackedData} chartConfig={chartConfig} />
            {viewMode === 'table' && (
              <SpendingTable data={stackedData} colorMap={colorMap} onCellClick={(cat, date) => setDrillDown({ category: cat, date })} />
            )}
          </div>
          <SpendingDrillDown
            open={drillDown !== null}
            category={drillDown?.category ?? ''}
            date={drillDown?.date ?? ''}
            events={events}
            onClose={() => setDrillDown(null)}
          />

          {/* Cumulative Spending (all years) */}
          <div className="bg-white rounded-xl border p-4 md:p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Cumulative Spending (Year over Year)</h2>
            <CumulativeSpendingChart data={categoryFilteredData} />
          </div>

        </div>
      )}
    </PageContainer>
  );
}
