import { SelectFilter } from "@/components/ui/select-filter";
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
    <SelectFilter
      label="Category"
      value={category}
      onChange={setCategory}
      options={CATEGORIES}
      placeholder="Select category"
    />
  );
}