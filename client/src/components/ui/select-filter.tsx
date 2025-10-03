import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import React from 'react';

interface SelectFilterProps<T extends string> {
  label: string;
  value: T;
  onChange: (value: T) => void;
  options: readonly T[];
  placeholder?: string;
}

export function SelectFilter<T extends string>({
  label,
  value,
  onChange,
  options,
  placeholder = `Select ${label.toLowerCase()}`
}: SelectFilterProps<T>) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent className="bg-white border">
          {options.map(option => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
