import React from 'react';
import { Form, InputGroup } from 'react-bootstrap';

// Define a constant array for years
const YEARS = [
  '2022',
  '2023',
  '2024'
] as const;

// Infer the Year type from the YEARS array
type Year = typeof YEARS[number];

interface YearFilterProps {
  year: Year;
  setYear: (year: Year) => void;
}

export default function YearFilter({ year, setYear }: YearFilterProps) {

  // Use React.ChangeEvent<HTMLSelectElement> for the event type
  const handleYearChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setYear(event.target.value as Year);
  }

  return (
    <>
      <InputGroup>
        <InputGroup.Text>Year</InputGroup.Text>
        <Form.Group controlId="exampleForm.SelectCustom">
          <Form.Select value={year} onChange={handleYearChange}>
            {YEARS.map(y => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
      </InputGroup>
    </>
  );
}
