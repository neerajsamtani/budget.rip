import React from 'react';

export default function PaymentMethodFilter({paymentMethod, setPaymentMethod}) {

  const handlePaymentMethodChange = (event) => {
    setPaymentMethod(event.target.value);
  }

  return (
    <form>
      <label>Payment Method</label>
      <select value={paymentMethod} onChange={handlePaymentMethodChange}>
        <option value="All">All</option>
        <option value="Checking">Checking</option>
        <option value="Credit">Credit</option>
        <option value="Savings">Savings</option>
        <option value="Splitwise">Splitwise</option>
        <option value="Stripe">Stripe</option>
        <option value="Venmo">Venmo</option>
      </select>
      </form>
  );
}