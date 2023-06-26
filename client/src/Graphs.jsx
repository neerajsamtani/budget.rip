import React, { useEffect, useState } from "react";
import axiosInstance from "./axiosInstance";
import Plot from 'react-plotly.js';

export default function Graphs() {

  const [categorizedData, setCategorizedData] = useState([])

  useEffect(() => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/monthly_breakdown`, { params: {} })
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
    <Plot
      data={data}
      layout={layout}
    />
  );
}