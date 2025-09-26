import React from 'react';
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Define a constant array for years
const YEARS = [
  '2022',
  '2023',
  '2024',
  '2025'
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
      <Label>Year</Label>
      <Select value={year} onValueChange={setYear}>
        <SelectTrigger>
          <SelectValue placeholder="Select year" />
        </SelectTrigger>
        <SelectContent>
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
