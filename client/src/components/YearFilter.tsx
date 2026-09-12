import { SelectFilter } from "@/components/ui/select-filter";
import React from 'react';

interface YearFilterProps {
  years: string[];
  year: string;

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
