import React from 'react';
import { Form, InputGroup } from 'react-bootstrap';

export default function PaymentMethodFilter({paymentMethod, setPaymentMethod}) {

  const handlePaymentMethodChange = (event) => {
    setPaymentMethod(event.target.value);
  }

  return (
    <>
    <InputGroup>
    <InputGroup.Text>Payment Method</InputGroup.Text>
      <Form.Group controlId="exampleForm.SelectCustom">
      <Form.Select value={paymentMethod} onChange={handlePaymentMethodChange}>
      <option value="All">All</option>
        {/* <option value="Checking">Checking</option>
        <option value="Credit">Credit</option>
        <option value="Savings">Savings</option> */}
        <option value="Splitwise">Splitwise</option>
        <option value="Stripe">Stripe</option>
        <option value="Venmo">Venmo</option>
      </Form.Select>
      </Form.Group>
    </InputGroup>
  </>
  );
}