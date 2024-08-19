import React from 'react';
import { Form, InputGroup } from 'react-bootstrap';

// Define a constant array for months
const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
  'All'
] as const;

// Infer the Month type from the MONTHS array
type Month = typeof MONTHS[number];

interface MonthFilterProps {
  month: Month;
  setMonth: (month: Month) => void;
}

export default function MonthFilter({ month, setMonth }: MonthFilterProps) {

  // Use React.ChangeEvent<HTMLSelectElement> for the event type
  const handleMonthChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setMonth(event.target.value as Month);
  }

  return (
    <>
      <InputGroup>
        <InputGroup.Text>Month</InputGroup.Text>
        <Form.Group controlId="exampleForm.SelectCustom">
          <Form.Select value={month} onChange={handleMonthChange}>
            {MONTHS.map(m => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
      </InputGroup>
    </>
  );
}
