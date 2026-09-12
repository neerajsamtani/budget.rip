import { Spinner } from "@/components/ui/spinner";
import { Table2 } from "lucide-react";
import { DateTime } from "luxon";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { buildChartConfig, filterByCategories, filterByYear, formatMonthYear, getAvailableYears, getLatestDate, NON_SPENDING_CATEGORIES, sumDisplayedAmounts } from "../components/charts/chart-utils";
import CumulativeSpendingChart from "../components/charts/CumulativeSpendingChart";
import SpendingDrillDown from "../components/charts/SpendingDrillDown";
import SpendingTable from "../components/charts/SpendingTable";
import StackedSpendingChart from "../components/charts/StackedSpendingChart";
import MultiSelectFilter from "../components/MultiSelectFilter";
import { Button } from "../components/ui/button";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import { CurrencyFormatter } from "../utils/formatters";
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

  const categoryNames = useMemo(() => {
    const dataNames = Object.keys(breakdownData).filter(category => Array.isArray(breakdownData[category]));
    return categories.length > 0 ? categories.map(category => category.name) : dataNames;
  }, [breakdownData, categories]);

  // Initialize selectedCategories once categories load — exclude Income and Investment by default
  const categoriesInitialized = useRef(false);
  useEffect(() => {
    if (categoryNames.length > 0 && !categoriesInitialized.current) {
      categoriesInitialized.current = true;
      setSelectedCategories(categoryNames.filter(n => !NON_SPENDING_CATEGORIES.includes(n)));
    }
  }, [categoryNames]);

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

  const hasRent = Array.isArray(breakdownData.Rent) && breakdownData.Rent.length > 0;
  const isRentSelected = selectedCategories.includes('Rent');
  const selectedYearTotal = useMemo(() => sumDisplayedAmounts(stackedData), [stackedData]);
  const latestDate = useMemo(() => getLatestDate(stackedData), [stackedData]);
  const categoryScope = selectedCategories.length === 0
    ? 'No categories selected'
    : `${selectedCategories.length} categor${selectedCategories.length === 1 ? 'y' : 'ies'} selected`;

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
              options={categoryNames.map(name => ({ id: name, name }))}
              selected={selectedCategories}
              onChange={setSelectedCategories}
            />
            {hasRent && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedCategories(prev => isRentSelected ? prev.filter(category => category !== 'Rent') : [...prev, 'Rent'])}
                aria-pressed={!isRentSelected}
              >
                {isRentSelected ? 'Exclude rent' : 'Include rent'}
              </Button>
            )}
          </div>

          <section aria-label="Chart summary" className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-muted-foreground">{year} spending</p>
              <p className="text-2xl font-semibold tabular-nums">
                {selectedCategories.length > 0 && Object.keys(stackedData).length > 0
                  ? CurrencyFormatter.format(selectedYearTotal)
                  : 'No data'}
              </p>
              <p className="text-sm text-muted-foreground">{categoryScope}</p>
            </div>
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-muted-foreground">Latest available month in {year}</p>
              <p className="text-2xl font-semibold tabular-nums">
                {latestDate ? formatMonthYear(latestDate) : 'No data'}
              </p>
              <p className="text-sm text-muted-foreground">Monthly Spending period</p>
            </div>
          </section>

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
            <p className="mb-4 text-sm text-muted-foreground">
              Monthly Spending uses the selected year and category scope: {categoryScope.toLowerCase()}.
            </p>
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
            <h2 className="text-lg font-semibold mb-2">Cumulative Spending (Year over Year)</h2>
            <p className="mb-4 text-sm text-muted-foreground">
              Cumulative Spending compares every available year for {categoryScope.toLowerCase()}. Each line ends at that year’s latest available month, so incomplete years are not presented as complete.
            </p>
            <CumulativeSpendingChart data={categoryFilteredData} />
          </div>

        </div>
      )}
    </PageContainer>
  );
}
