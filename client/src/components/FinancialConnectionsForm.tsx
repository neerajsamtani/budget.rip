import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  useStripe
} from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import React, { useState } from "react";
import axiosInstance from "../utils/axiosInstance";
import { showErrorToast, showSuccessToast } from "../utils/toast-helpers";

export default function FinancialConnectionsForm({ fcsess_secret, setStripeAccounts }:
  // eslint-disable-next-line no-unused-vars
  { fcsess_secret: string, setStripeAccounts: (accounts: FinancialConnectionsSession.Account[]) => void }) {
  const stripe = useStripe();


  const [isLoading, setIsLoading] = useState(false);

  const storeAccounts = (accounts: FinancialConnectionsSession.Account[]) => {
    axiosInstance.post(`api/create_accounts`, accounts)
      .then(response => showSuccessToast(response.data, "Accounts Created"))
      .catch(showErrorToast);
  }

  const handleSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();

    if (!stripe) {
      // Stripe.js has not yet loaded.
      // Make sure to disable form submission until Stripe.js has loaded.
      return;
    }

    setIsLoading(true);
    const financialConnectionsSessionResult = await stripe.collectFinancialConnectionsAccounts({ clientSecret: fcsess_secret });

    if (financialConnectionsSessionResult.error) {
      showErrorToast(new Error(`${financialConnectionsSessionResult.error.message} Please refresh the page and try again.`));
    } else if (financialConnectionsSessionResult.financialConnectionsSession.accounts.length === 0) {
      showErrorToast(new Error("No new accounts were linked"));
    } else {
      const returnedAccounts = financialConnectionsSessionResult.financialConnectionsSession.accounts
      setStripeAccounts(returnedAccounts)
      storeAccounts(returnedAccounts)
    }

    setIsLoading(false);
  };

  return (
    <>
      <Button onClick={handleSubmit} disabled={isLoading || !stripe} id="submit">
        <span id="button-text">
          {isLoading ?
            <Spinner
              size="sm"
            />
            :
            "Connect your bank"}
        </span>
      </Button>
    </>
  );
}