import {
  useStripe
} from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import React, { useState } from "react";
import { Button, Spinner } from 'react-bootstrap';
import axiosInstance from "../utils/axiosInstance";
import Notification from "./Notification";

export default function FinancialConnectionsForm({ fcsess_secret, setStripeAccounts }:
  { fcsess_secret: string, setStripeAccounts: (accounts: FinancialConnectionsSession.Account[]) => void }) {
  const stripe = useStripe();

  const [notification, setNotification] = useState(
    {
      heading: "Error",
      message: "",
      showNotification: false,
    }
  )

  const [isLoading, setIsLoading] = useState(false);

  const storeAccounts = (accounts: FinancialConnectionsSession.Account[]) => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    axiosInstance.post(`${REACT_APP_API_ENDPOINT}api/create_accounts`, accounts)
      .then(response => console.log(response.data))
      .catch(error => console.log(error));
  }

  const handleSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
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
      setNotification({
        ...notification,
        message: `${financialConnectionsSessionResult.error.message} Please refresh the page and try again.`,
        showNotification: true
      })
    } else if (financialConnectionsSessionResult.financialConnectionsSession.accounts.length === 0) {
      setNotification({
        ...notification,
        message: "No new accounts were linked",
        showNotification: true
      })
    } else {
      var returnedAccounts = financialConnectionsSessionResult.financialConnectionsSession.accounts
      setStripeAccounts(returnedAccounts)
      storeAccounts(returnedAccounts)
    }

    setIsLoading(false);
  };

  return (
    <>
      <Notification notification={notification} setNotification={setNotification} />
      <Button onClick={handleSubmit} disabled={isLoading || !stripe} id="submit" variant="primary">
        <span id="button-text">
          {isLoading ?
            <Spinner
              as="span"
              animation="border"
              size="sm"
              role="status"
              aria-hidden="true"
              data-testid="spinner"
            />
            :
            "Connect your bank"}
        </span>
      </Button>
    </>
  );
}