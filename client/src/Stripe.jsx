import React, {useState, useEffect} from "react";
import { Elements } from "@stripe/react-stripe-js";
import axios from "axios";
import FinancialConnectionsForm from "./FinancialConnectionsForm";
import { Button } from "react-bootstrap";

export default function Stripe({stripePromise}) {

    const [clientSecret, setClientSecret] = useState("");
    const [stripeAccounts, setStripeAccounts] = useState([])
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);

    const createSession = () => {
        axios.post(`${REACT_APP_API_ENDPOINT}api/create-fc-session`)
            .then(response => setClientSecret(response.data.clientSecret))
            .catch(error => console.log(error));
      }

    const subscribeToAccounts = () => {
        if (stripeAccounts) {
          for (var account of stripeAccounts) {
            axios.get(`${REACT_APP_API_ENDPOINT}api/subscribe_to_account/${account.id}`)
            .then(response => console.log(response.data))
          }
        }
      }

    const appearance = {
        theme: 'stripe',
      };
      const options = {
        // clientSecret,
        appearance,
      };

    return(
        <div>
            <h1>Stripe Connection</h1>
            {/* {stripeAccounts && <div id="stripeAccounts">stripeAccounts: {JSON.stringify(stripeAccounts, null, 2)}</div>} */}
            {stripeAccounts && 
                <div id="stripeAccounts"> {stripeAccounts.length > 0 ?
                    <>
                        <p>Bank Accounts Linked:</p>
                        <ul>{stripeAccounts.map(account => <li key={account.id}>{account.id} | {account.institution_name} {account.subcategory}</li>)}</ul>
                    </>
                    : "No Bank Accounts Linked"}
                </div>}
            <div className="Form">
                {!clientSecret &&
                (<Button onClick={createSession}>
                    Create FC Session
                </Button>
                )}
                {clientSecret && (
                    <Elements options={options} stripe={stripePromise}>
                    <FinancialConnectionsForm fcsess_secret={clientSecret} setStripeAccounts={setStripeAccounts} />
                    </Elements>
                )}
                {stripeAccounts.length > 0 &&
                (<Button onClick={subscribeToAccounts}>
                    Subscribe to Accounts
                </Button>
                )}
            </div>
        </div>
    )
}