import React, { useEffect, useState, lazy, Suspense } from "react";
import axiosInstance from "../utils/axiosInstance";

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
    var VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    axiosInstance.get(`${VITE_API_ENDPOINT}api/monthly_breakdown`, { params: {} })
      .then(response => {
        setCategorizedData(response.data)
      })
      .catch(error => console.log(error));
  }, [])

  const data = Object.keys(categorizedData).map((category) => {
    const amounts = categorizedData[category].map((item) => item.amount);
    return {
      x: categorizedData[category].map((item) => item.date),
      y: amounts,
      type: 'bar',
      name: category,
    };
  });

  const layout = {
    barmode: 'relative',
    xaxis: { title: 'Date' },
    yaxis: { title: 'Amount' },
    width: 1000,
    height: 600
  };


  return (
    <Suspense fallback={<div>Loading chart...</div>}>
      <Plot
        data={data}
        layout={layout}
      />
    </Suspense>
  );
}