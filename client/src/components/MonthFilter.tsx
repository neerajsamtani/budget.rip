import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
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
    <div className="space-y-2">
      <Label>Month</Label>
      <Select value={month} onValueChange={setMonth}>
        <SelectTrigger>
          <SelectValue placeholder="Select month" />
        </SelectTrigger>
        <SelectContent>
          {MONTHS.map(m => (
            <SelectItem key={m} value={m}>
              {m}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
