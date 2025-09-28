import React, { lazy, Suspense, useEffect, useState } from "react";
import axiosInstance from "../utils/axiosInstance";
import { chartColorSequence } from '../lib/chart-colors';
import { PageContainer, PageHeader } from "../components/ui/layout";
import { H1, Body } from "../components/ui/typography";

const Plot = lazy(() => import('react-plotly.js'));

interface Expense {
  amount: number;
  date: string;
}

interface CategoryExpense {
  [key: string]: Expense[];
}

export default function GraphsPage() {

  const [categorizedData, setCategorizedData] = useState<CategoryExpense>({})

  useEffect(() => {
    const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    axiosInstance.get(`${VITE_API_ENDPOINT}api/monthly_breakdown`, { params: {} })
      .then(response => {
        setCategorizedData(response.data)
      })
      .catch(error => console.log(error));
  }, [])

  const data = Object.keys(categorizedData).map((category, index) => {
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
      title: 'Date',
      gridcolor: '#F5F5F5',
      linecolor: '#E0E0E0',
    },
    yaxis: {
      title: 'Amount',
      gridcolor: '#F5F5F5',
      linecolor: '#E0E0E0',
    },
    width: 1000,
    height: 600,
    // Nordic styling
    paper_bgcolor: '#FFFFFF',
    plot_bgcolor: '#FFFFFF',
    font: {
      family: 'Source Sans Pro, sans-serif',
      size: 12,
      color: '#374151'
    },
    colorway: chartColorSequence
  };


  return (
    <PageContainer>
      <PageHeader>
        <H1>Graphs</H1>
        <Body className="text-[#6B7280]">
          Visual analysis of your spending patterns and financial trends
        </Body>
      </PageHeader>

      <div className="space-y-6">
        <div className="bg-white rounded-xl border border-[#E0E0E0] p-6 shadow-sm">
          <Suspense fallback={
            <div className="flex items-center justify-center h-96">
              <Body className="text-[#6B7280]">Loading chart...</Body>
            </div>
          }>
            <Plot
              data={data}
              layout={layout}
              config={{
                displayModeBar: false,
                responsive: true
              }}
              style={{ width: '100%', height: '600px' }}
            />
          </Suspense>
        </div>
      </div>
    </PageContainer>
  );
}