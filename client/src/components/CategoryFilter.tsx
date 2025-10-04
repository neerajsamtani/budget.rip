import { SelectFilter } from "@/components/ui/select-filter";
import React from 'react';
import { CATEGORIES, Category } from '@/constants/categories';

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