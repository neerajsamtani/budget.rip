import { SelectFilter } from "@/components/ui/select-filter";
import React from 'react';

interface YearFilterProps {
  years: string[];
  year: string;
  // eslint-disable-next-line no-unused-vars
  setYear: (year: string) => void;
}

export default function YearFilter({ years, year, setYear }: YearFilterProps) {
  return (
    <SelectFilter
      label="Year"
      value={year}
      onChange={setYear}
      options={years}
      placeholder="Select year"
    />
  );
}
