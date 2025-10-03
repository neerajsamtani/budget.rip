import { SelectFilter } from "@/components/ui/select-filter";
import React from 'react';

// Define a constant array for months
const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
  'All'
] as const;

// Infer the Month type from the MONTHS array
type Month = typeof MONTHS[number];

interface MonthFilterProps {
  month: Month;
  // eslint-disable-next-line no-unused-vars
  setMonth: (month: Month) => void;
}

export default function MonthFilter({ month, setMonth }: MonthFilterProps) {
  return (
    <SelectFilter
      label="Month"
      value={month}
      onChange={setMonth}
      options={MONTHS}
      placeholder="Select month"
    />
  );
}
