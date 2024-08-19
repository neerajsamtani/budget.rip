import React, { useState, useEffect } from "react";
import { Form, InputGroup } from 'react-bootstrap';
import axiosInstance from "./axiosInstance";

type PaymentMethod = string
interface PaymentMethodFilterProps {
  paymentMethod: PaymentMethod,
  setPaymentMethod: (paymentMethod: PaymentMethod) => void
}

export default function PaymentMethodFilter({ paymentMethod, setPaymentMethod }: PaymentMethodFilterProps) {

  const [paymentMethods, setPaymentMethods] = useState([])

  useEffect(() => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/payment_methods`)
      .then(response => {
        setPaymentMethods(response.data)
      })
      .catch(error => console.log(error));
  }, [])

  const handlePaymentMethodChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setPaymentMethod(event.target.value);
  }

  return (
    <>
      <InputGroup>
        <InputGroup.Text>Payment Method</InputGroup.Text>
        <Form.Group controlId="exampleForm.SelectCustom">
          <Form.Select value={paymentMethod} onChange={handlePaymentMethodChange}>
            <option value="All">All</option>
            {paymentMethods.map(payment_method => {
              return (<option value={payment_method} key={payment_method}> {payment_method}</option>)
            })}
          </Form.Select>
        </Form.Group>
      </InputGroup>
    </>
  );
}