import { Spinner } from "@/components/ui/spinner";
import { DateTime } from "luxon";
import { BarChart2, Table2 } from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";
import CumulativeSpendingChart from "../components/charts/CumulativeSpendingChart";
import { filterByCategories, filterByYear } from "../components/charts/chart-utils";
import SpendingDrillDown from "../components/charts/SpendingDrillDown";
import SpendingTable from "../components/charts/SpendingTable";
import StackedSpendingChart from "../components/charts/StackedSpendingChart";
import { Button } from "../components/ui/button";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import YearFilter, { type Year } from "../components/YearFilter";
import { useCategories, useEvents, useMonthlyBreakdown } from "../hooks/useApi";
import MultiSelectFilter from "../components/MultiSelectFilter";

export default function GraphsPage() {
  const [year, setYear] = useState<Year>(() => String(DateTime.utc().year) as Year);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');
  const [drillDown, setDrillDown] = useState<{ category: string; date: string } | null>(null);

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
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Monthly Spending by Category</h2>
              <div className="flex rounded-md border overflow-hidden">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setViewMode('chart')}
                  className={viewMode === 'chart' ? 'bg-muted' : ''}
                >
                  <BarChart2 className="size-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setViewMode('table')}
                  className={viewMode === 'table' ? 'bg-muted' : ''}
                >
                  <Table2 className="size-4" />
                </Button>
              </div>
            </div>
            <StackedSpendingChart data={stackedData} />
            {viewMode === 'table' && (
              <SpendingTable data={stackedData} onCellClick={(cat, date) => setDrillDown({ category: cat, date })} />
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
