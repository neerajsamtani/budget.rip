import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import React from 'react';

// Keep this in sync with the server/constants.py
// Define a constant array for categories
const CATEGORIES = [
  'All',
  'Alcohol',
  'Dining',
  'Entertainment',
  'Forma',
  'Groceries',
  'Hobbies',
  'Income',
  'Investment',
  'Medical',
  'Rent',
  'Shopping',
  'Subscription',
  'Transfer',
  'Transit',
  'Travel'
] as const;

// Infer the Category type from the CATEGORIES array
export type Category = typeof CATEGORIES[number];

// eslint-disable-next-line no-unused-vars
export default function CategoryFilter({ category, setCategory }: { category: Category, setCategory: (category: Category) => void }) {


  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium text-foreground">Category</Label>
      <Select value={category} onValueChange={setCategory}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select category" />
        </SelectTrigger>
        <SelectContent className="bg-white border">
          {CATEGORIES.map(cat => (
            <SelectItem key={cat} value={cat}>
              {cat}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}