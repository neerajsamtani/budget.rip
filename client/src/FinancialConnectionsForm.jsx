import React, { useState } from "react";
import {
  useStripe
} from "@stripe/react-stripe-js";
import axios from "axios";
import { Button, Spinner, ToastContainer, Toast } from 'react-bootstrap';

export default function FinancialConnectionsForm({ fcsess_secret, setStripeAccounts }) {
  const stripe = useStripe();

  const [message, setMessage] = useState("");
  const [showMessage, setShowMessage] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const toggleShowMessage = () => setShowMessage(!showMessage);

  const storeAccounts = (accounts) => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    axios.post(`${REACT_APP_API_ENDPOINT}api/create_accounts`, accounts)
      .then(response => console.log(response.data))
      .catch(error => console.log(error));
  }

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!stripe) {
      // Stripe.js has not yet loaded.
      // Make sure to disable form submission until Stripe.js has loaded.
      return;
    }

    setIsLoading(true);

    // console.log("The client secret is", fcsess_secret)
    const financialConnectionsSessionResult = await stripe.collectFinancialConnectionsAccounts({ clientSecret: fcsess_secret });

    console.log(financialConnectionsSessionResult);

    // This point will only be reached if there is an immediate error when
    // confirming the payment. Otherwise, your customer will be redirected to
    // your `return_url`. For some payment methods like iDEAL, your customer will
    // be redirected to an intermediate site first to authorize the payment, then
    // redirected to the `return_url`.
    if (financialConnectionsSessionResult.error) {
      setMessage(`${financialConnectionsSessionResult.error.message} Please refresh the page and try again.`);
      setShowMessage(true)
    } else if (financialConnectionsSessionResult.financialConnectionsSession.accounts.length === 0) {
      setMessage("No new accounts were linked")
      setShowMessage(true)
    } else {
      var returnedAccounts = financialConnectionsSessionResult.financialConnectionsSession.accounts
      setStripeAccounts(returnedAccounts)
      storeAccounts(returnedAccounts)
    }

    setIsLoading(false);
  };

  return (
    <>
      <ToastContainer className="p-3" position='top-end'>
        <Toast show={showMessage} onClose={toggleShowMessage} delay={3500} autohide>
          <Toast.Header>
            <strong className="me-auto">Error</strong>
          </Toast.Header>
          <Toast.Body>{message}</Toast.Body>
        </Toast>
      </ToastContainer>
      <Button onClick={handleSubmit} disabled={isLoading || !stripe} id="submit" variant="primary">
        <span id="button-text">
          {isLoading ?
            <Spinner
              as="span"
              animation="border"
              size="sm"
              role="status"
              aria-hidden="true"
            />
            :
            "Connect your bank"}
        </span>
      </Button>
    </>
  );
}