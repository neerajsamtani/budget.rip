import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
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
type Year = typeof YEARS[number];

interface YearFilterProps {
  year: Year;
  // eslint-disable-next-line no-unused-vars
  setYear: (year: Year) => void;
}

export default function YearFilter({ year, setYear }: YearFilterProps) {


  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium text-foreground">Year</Label>
      <Select value={String(year)} onValueChange={setYear}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select year" />
        </SelectTrigger>
        <SelectContent className="bg-white border">
          {YEARS.map(y => (
            <SelectItem key={y} value={y}>
              {y}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
