import React from 'react';
import { Form, InputGroup } from 'react-bootstrap';

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
  'Rent',
  'Shopping',
  'Subscription',
  'Transfer',
  'Transit',
  'Travel'
] as const;

// Infer the Category type from the CATEGORIES array
export type Category = typeof CATEGORIES[number];

export default function CategoryFilter({ category, setCategory }: { category: Category, setCategory: (category: Category) => void }) {

  const handleCategoryChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setCategory(event.target.value as Category);
  }

  return (
    <>
      <InputGroup>
        <InputGroup.Text>Category</InputGroup.Text>
        <Form.Group controlId="exampleForm.SelectCustom">
          <Form.Select value={category} onChange={handleCategoryChange}>
            {CATEGORIES.map(cat => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
      </InputGroup>
    </>
  );
}