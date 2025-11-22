import React, { lazy, Suspense, useState, useEffect } from "react";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import { chartColorSequence } from '../lib/chart-colors';
import { useMonthlyBreakdown } from "../hooks/useApi";

const Plot = lazy(() => import('react-plotly.js'));

interface Expense {
  amount: number;
  date: string;
}

interface CategoryExpense {
  [key: string]: Expense[];
}

export default function GraphsPage() {
  const { data: categorizedData = {}, isLoading, error } = useMonthlyBreakdown()
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const data = Object.keys(categorizedData)
    .filter(category => Array.isArray(categorizedData[category]))
    .map((category, index) => {
      const amounts = categorizedData[category].map((item) => item.amount);
      return {
        x: categorizedData[category].map((item) => item.date),
        y: amounts,
        type: 'bar',
        name: category,
        marker: {
          color: chartColorSequence[index % chartColorSequence.length]
        }
      };
    });

  const layout = {
    barmode: 'relative',
    xaxis: {
      title: isMobile ? '' : 'Date',
      gridcolor: '#F5F5F5',
      linecolor: '#E0E0E0',
      tickangle: isMobile ? -45 : 0,
      tickfont: { size: isMobile ? 9 : 12 },
      nticks: isMobile ? 6 : undefined,
    },
    yaxis: {
      title: isMobile ? '' : 'Amount',
      gridcolor: '#F5F5F5',
      linecolor: '#E0E0E0',
      tickfont: { size: isMobile ? 10 : 12 },
    },
    autosize: true,
    margin: isMobile
      ? { l: 40, r: 10, t: 10, b: 60 }
      : { l: 60, r: 30, t: 30, b: 60 },
    // Nordic styling
    paper_bgcolor: '#FFFFFF',
    plot_bgcolor: '#FFFFFF',
    font: {
      family: 'Source Sans Pro, sans-serif',
      size: isMobile ? 10 : 12,
      color: '#374151'
    },
    colorway: chartColorSequence,
    legend: isMobile ? {
      orientation: 'h',
      y: -0.3,
      x: 0.5,
      xanchor: 'center',
      font: { size: 10 },
    } : {
      orientation: 'v',
      y: 0.5,
      x: 1.02,
      xanchor: 'left',
    },
    showlegend: true,
  };


  return (
    <PageContainer>
      <PageHeader>
        <H1>Graphs</H1>
        <Body className="text-muted-foreground">
          Visual analysis of your spending patterns and financial trends
        </Body>
      </PageHeader>

      <div className="space-y-6">
        <div className="bg-white rounded-xl border p-2 md:p-6 shadow-sm overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-64 md:h-96">
              <Body className="text-muted-foreground">Loading data...</Body>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64 md:h-96">
              <Body className="text-destructive">Error loading data. Please try again.</Body>
            </div>
          ) : (
            <Suspense fallback={
              <div className="flex items-center justify-center h-64 md:h-96">
                <Body className="text-muted-foreground">Loading chart...</Body>
              </div>
            }>
              <Plot
                data={data}
                layout={layout}
                config={{
                  displayModeBar: false,
                  responsive: true,
                  scrollZoom: false,
                }}
                style={{
                  width: '100%',
                  height: isMobile ? '350px' : '500px',
                }}
                useResizeHandler={true}
                className="w-full"
              />
            </Suspense>
          )}
        </div>
      </div>
    </PageContainer>
  );
}