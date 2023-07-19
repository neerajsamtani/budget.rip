import React, { useState, useEffect, Fragment } from "react";
import { Elements } from "@stripe/react-stripe-js";
import axiosInstance from "./axiosInstance";
import FinancialConnectionsForm from "./FinancialConnectionsForm";
import { Button } from "react-bootstrap";
import { Table } from "react-bootstrap";
import Notification from "./Notification";

export default function ConnectedAccounts({ stripePromise }) {

    const [connectedAccounts, setConnectedAccounts] = useState([])
    const [clientSecret, setClientSecret] = useState("");
    const [stripeAccounts, setStripeAccounts] = useState([])
    const [notification, setNotification] = useState(
        {
            heading: "Notification",
            message: "",
            showNotification: false,
        }
    )

    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/connected_accounts`)
            .then(response => {
                setConnectedAccounts(response.data)
            })
            .catch(error => console.log(error));
    }, [])

    const createSession = () => {
        axiosInstance.post(`${REACT_APP_API_ENDPOINT}api/create-fc-session`)
            .then(response => setClientSecret(response.data.clientSecret))
            .catch(error => console.log(error));
    }

    const subscribeToAccounts = () => {
        if (stripeAccounts) {
            for (var account of stripeAccounts) {
                axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/subscribe_to_account/${account.id}`)
                    .then(response => console.log(response.data))
            }
        }
        setClientSecret("")
        setStripeAccounts([])
        setNotification({
            ...notification,
            message: "Subscribing to the accounts provided. Please refresh the page.",
            showNotification: true
        })
    }

    const appearance = {
        theme: 'stripe',
    };
    const options = {
        // clientSecret,
        appearance,
    };

    return (
        <>
            <div>
                <h1>Connected Accounts</h1>
                <Notification notification={notification} setNotification={setNotification} />
                <div className="Form">
                    {clientSecret ?
                        stripeAccounts.length > 0 ?
                            <Fragment>
                                <Table striped bordered hover>
                                    <thead>
                                        <tr>
                                            <th>Bank Accounts Received:</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {
                                            stripeAccounts
                                                .map(account => (
                                                    <tr key={account.id}>
                                                        <td>
                                                            {account.institution_name} {account.subcategory} ({account.id})
                                                        </td>
                                                    </tr>
                                                ))
                                        }
                                    </tbody>
                                </Table>
                                <Button onClick={subscribeToAccounts}>
                                    Subscribe to these accounts
                                </Button>
                            </Fragment>
                            :
                            <Elements options={options} stripe={stripePromise}>
                                <FinancialConnectionsForm fcsess_secret={clientSecret} setStripeAccounts={setStripeAccounts} />
                            </Elements>
                        :
                        <Button onClick={createSession}>
                            Connect A New Account
                        </Button>
                    }
                </div>
                <div id="stripeAccounts">

                </div>
            </div>
            <br />
            <div>
                <Table striped bordered hover>
                    <thead>
                        <tr>
                            <th>Connected Accounts</th>
                        </tr>
                    </thead>
                    <tbody>
                        {connectedAccounts.length > 0 ?
                            connectedAccounts
                                .map(connectedAccount => (
                                    <tr key={connectedAccount}>
                                        <td>
                                            {connectedAccount}
                                        </td>
                                    </tr>
                                ))
                            :
                            <tr align="center">
                                <td colSpan="4">
                                    No connected accounts found
                                </td>
                            </tr>
                        }
                    </tbody>
                </Table>
            </div>
        </>
    )
}