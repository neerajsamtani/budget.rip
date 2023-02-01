import React from 'react';

export default function CategoryFilter({category, setCategory}) {

  const handleCategoryChange = (event) => {
    setCategory(event.target.value);
  }

  return (
    <form>
      <label>Category</label>
          <select value={category} onChange={handleCategoryChange}>
            <option value="All">All</option>
            <option value="Alcohol">Alcohol</option>
            <option value="Dining">Dining</option>
            <option value="Entertainment">Entertainment</option>
            <option value="Groceries">Groceries</option>
            <option value="Hobbies">Hobbies</option>
            <option value="Income">Income</option>
            <option value="N/A">N/A</option>
            <option value="Rent">Rent</option>
            <option value="Shopping">Shopping</option>
            <option value="Subscription">Subscription</option>
            <option value="Transit">Transit</option>
            <option value="Travel">Travel</option>
          </select>
      </form>
  );
}