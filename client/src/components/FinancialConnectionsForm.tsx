import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  useStripe
} from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import React, { useState } from "react";
import { toast } from "sonner";
import axiosInstance from "../utils/axiosInstance";

export default function FinancialConnectionsForm({ fcsess_secret, setStripeAccounts }:
  // eslint-disable-next-line no-unused-vars
  { fcsess_secret: string, setStripeAccounts: (accounts: FinancialConnectionsSession.Account[]) => void }) {
  const stripe = useStripe();


  const [isLoading, setIsLoading] = useState(false);

  const storeAccounts = (accounts: FinancialConnectionsSession.Account[]) => {
    const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    axiosInstance.post(`${VITE_API_ENDPOINT}api/create_accounts`, accounts)
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
      toast("Error", {
        description: `${financialConnectionsSessionResult.error.message} Please refresh the page and try again.`,
        duration: 3500,
      });
    } else if (financialConnectionsSessionResult.financialConnectionsSession.accounts.length === 0) {
      toast.error("Error", {
        description: "No new accounts were linked",
        duration: 3500,
      });
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