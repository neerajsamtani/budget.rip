import { SelectFilter } from "@/components/ui/select-filter";
import React from 'react';
import { useCategories } from '../hooks/useApi';

export default function CategoryFilter({ category, setCategory }: { category: string, setCategory: (category: string) => void }) {
  const { data: categories = [], isLoading, isError } = useCategories();

  // "All" is a special filter value (not a real category in DB)
  // Used to show all events regardless of category
  const options = ['All', ...categories.map(c => c.name)];

  const getPlaceholder = () => {
    if (isLoading) return "Loading...";
    if (isError) return "Error loading categories";
    return "Select category";
  };

  return (
    <SelectFilter
      label="Category"
      value={category}
      onChange={setCategory}
      options={options}
      placeholder={getPlaceholder()}
    />
  );
}