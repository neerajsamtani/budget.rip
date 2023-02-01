import React from 'react';

export default function MonthFilter({month, setMonth}) {

  const handleMonthChange = (event) => {
    setMonth(event.target.value);
  }

  return (
    <form>
      <label>Month</label>
          <select value={month} onChange={handleMonthChange}>
            <option value="January">January</option>
            <option value="February">February</option>
            <option value="March">March</option>
            <option value="April">April</option>
            <option value="May">May</option>
            <option value="June">June</option>
            <option value="July">July</option>
            <option value="August">August</option>
            <option value="September">September</option>
            <option value="October">October</option>
            <option value="November">November</option>
            <option value="December">December</option>
            <option value="All">All</option>
          </select>
      </form>
  );
}