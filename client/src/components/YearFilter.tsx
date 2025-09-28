import React from 'react';
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

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
  setYear: (year: Year) => void;
}

export default function YearFilter({ year, setYear }: YearFilterProps) {


  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium text-[#374151]">Year</Label>
      <Select value={year} onValueChange={setYear}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select year" />
        </SelectTrigger>
        <SelectContent className="bg-white border border-[#E0E0E0]">
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
