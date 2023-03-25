import React, { useEffect, useState } from "react";
import axios from "axios";
import { VictoryChart, VictoryLine, VictoryAxis, VictoryVoronoiContainer, VictoryLegend, VictoryLabel, VictoryTheme } from 'victory';
import { scaleOrdinal } from 'd3-scale';

export default function App() {

  const [monthly_breakdown, setMonthlyBreakdown] = useState([])

  var stringToColour = (str = "") => {
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    var colour = '#';
    for (var i = 0; i < 3; i++) {
      var value = (hash >> (i * 8)) & 0xFF;
      colour += ('00' + value.toString(16)).substr(-2);
    }
    return colour;
  }

  useEffect(() => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    axios.get(`${REACT_APP_API_ENDPOINT}api/monthly_breakdown`, { params: {}})
    .then(response => {
      setMonthlyBreakdown(response.data)
      console.log(response.data)
    })
    .catch(error => console.log(error));
}, [])

  const dataArray = Object.entries(monthly_breakdown); // Convert object to array of key-value pairs
  // const getCategories = () => {
  //   dates  = []
  //   for (item in monthly_breakdown["Dining"]) {
  //     dates += item["date"]
  //   }
  //   return dates.sort()
  //   // TODO
  // }
  const categories = ["8-2022", "9-2022", "10-2022", "11-2022", "12-2022", "1-2023", "2-2023", "3-2023"];

  return (
    <>
    <VictoryChart width={800} height={300}
      domainPadding={{ x: 20, y: 10 }}
      theme={VictoryTheme.material}
      containerComponent={
        <VictoryVoronoiContainer
          labels={({ datum }) => `${Math.round(datum.amount, 2)}`}
        />
      }
      >
      <VictoryLegend x={50} y={10}
      style={{ border: { stroke: "black" }, title: { fontSize: 12 } }}
        orientation="horizontal"
        gutter={20}
        data={dataArray &&
          dataArray.map(([key, value]) => {
            return { name: key, symbol: { fill: stringToColour(key) } };
          })
        }
      />
      {/* <VictoryAxis
        tickValues={data.map(d => `${d.month} ${d.year}`)}
        tickFormat={(year) => year}
        style={{
          axisLabel: { padding: 35 },
          ticks: { padding: 5 },
          tickLabels: { angle: 45 },
        }}
      />
      <VictoryAxis
        dependentAxis
        tickFormat={(x) => (`$${x / 1000}k`)}
      /> */}
      {dataArray.map(([key, value]) => 
      { if (key !== "Income" && key !== "Rent")
        return (
        <VictoryLine
        interpolation="linear"
        data={value}
        x="date"
        y="amount"
        style={{
          data: { stroke: stringToColour(key),},
        }}
      />
      )}
      )}
    </VictoryChart>
    </>
  );
}