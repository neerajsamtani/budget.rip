import React from 'react';

export default function YearFilter({year, setYear}) {

  const handleYearChange = (event) => {
    setYear(event.target.value);
  }

  return (
    <form>
      <label>Year</label>
          <select value={year} onChange={handleYearChange}>
            <option value="2022">2022</option>
            <option value="2023">2023</option>
          </select>
      </form>
  );
}