import React from 'react';
import { Form, InputGroup } from 'react-bootstrap';

export default function YearFilter({ year, setYear }) {

  const handleYearChange = (event) => {
    setYear(event.target.value);
  }

  return (
    <>
      <InputGroup>
        <InputGroup.Text>Year</InputGroup.Text>
        <Form.Group controlId="exampleForm.SelectCustom">
          <Form.Select value={year} onChange={handleYearChange}>
            <option value="2022">2022</option>
            <option value="2023">2023</option>
          </Form.Select>
        </Form.Group>
      </InputGroup>
    </>
  );
}