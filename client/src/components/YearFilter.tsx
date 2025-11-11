import { SelectFilter } from "@/components/ui/select-filter";
import React from 'react';

// Define a constant array for years
const YEARS = [
  '2022',
  '2023',
  '2024',
  '2025',
  '2026'
] as const;

// Infer the Year type from the YEARS array
export type Year = typeof YEARS[number];

interface YearFilterProps {
  year: Year;
  // eslint-disable-next-line no-unused-vars
  setYear: (year: Year) => void;
}

export default function YearFilter({ year, setYear }: YearFilterProps) {
  return (
    <SelectFilter
      label="Year"
      value={year}
      onChange={setYear}
      options={YEARS}
      placeholder="Select year"
    />
  );
}
