import { SelectFilter } from "@/components/ui/select-filter";
import React from 'react';
import { useCategories } from '../hooks/useApi';

export default function CategoryFilter({ category, setCategory }: { category: string, setCategory: (category: string) => void }) {
  const { data: categories = [], isLoading } = useCategories();

  // Build options array with "All" at the beginning for filtering
  const options = ['All', ...categories.map(c => c.name)];

  return (
    <SelectFilter
      label="Category"
      value={category}
      onChange={setCategory}
      options={options}
      placeholder={isLoading ? "Loading..." : "Select category"}
    />
  );
}