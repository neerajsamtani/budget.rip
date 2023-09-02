import React from 'react';
import { Form, InputGroup } from 'react-bootstrap';

export default function CategoryFilter({ category, setCategory }) {

  const handleCategoryChange = (event) => {
    setCategory(event.target.value);
  }

  return (
    <>
      <InputGroup>
        <InputGroup.Text>Category</InputGroup.Text>
        <Form.Group controlId="exampleForm.SelectCustom">
          <Form.Select value={category} onChange={handleCategoryChange}>
            <option value="All">All</option>
            <option value="Alcohol">Alcohol</option>
            <option value="Dining">Dining</option>
            <option value="Entertainment">Entertainment</option>
            <option value="Expenses">Expenses</option>
            <option value="Forma">Forma</option>
            <option value="Groceries">Groceries</option>
            <option value="Hobbies">Hobbies</option>
            <option value="Income">Income</option>
            <option value="N/A">N/A</option>
            <option value="Rent">Rent</option>
            <option value="Shopping">Shopping</option>
            <option value="Subscription">Subscription</option>
            <option value="Transit">Transit</option>
            <option value="Travel">Travel</option>
          </Form.Select>
        </Form.Group>
      </InputGroup>
    </>
  );
}