import { Elements } from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import { Stripe } from "@stripe/stripe-js/types/stripe-js";
import React, { Fragment, useEffect, useState } from "react";
import { Button, Table } from "react-bootstrap";
import FinancialConnectionsForm from "../components/FinancialConnectionsForm";
import Notification from "../components/Notification";
import axiosInstance from "../utils/axiosInstance";

export default function ConnectedAccountsPage({ stripePromise }: { stripePromise: Promise<Stripe | null> }) {

    const [connectedAccounts, setConnectedAccounts] = useState([])
    const [accountsAndBalances, setAccountsAndBalances] = useState({})
    const [clientSecret, setClientSecret] = useState("");
    const [stripeAccounts, setStripeAccounts] = useState<FinancialConnectionsSession.Account[]>([])
    const [notification, setNotification] = useState(
        {
            heading: "Notification",
            message: "",
            showNotification: false,
        }
    )

    const currencyFormatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
    });
    const formatBalance = (balance: number) => currencyFormatter.format(balance)

    const dateFormatter = new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        timeZone: "UTC"
    });
    const formatDate = (unixTime: number) => dateFormatter.format(new Date(unixTime * 1000))

    let netWorth = 0;
    // Only active accounts are included in the net worth calculation
    Object.keys(accountsAndBalances).forEach(key => {
        if (accountsAndBalances[key]["status"] === "active") {
            netWorth += accountsAndBalances[key]["balance"]
        }
    })

    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/connected_accounts`)
            .then(response => {
                setConnectedAccounts(response.data)
            })
            .catch(error => console.log(error));
        axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/accounts_and_balances`)
            .then(response => {
                setAccountsAndBalances(response.data)
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

    const relinkAccount = (accountId) => {
        axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/relink_account/${accountId}`)
            .then(response => setClientSecret(response.data.clientSecret))
            .catch(error => console.log(error));
    }

    const appearance = {
        theme: 'stripe' as const,
    };
    const options = {
        // clientSecret,
        appearance,
    };

    const renderConnectedAccount = (connectedAccount) => {
        // Handle Venmo data (array)
        if (connectedAccount.venmo) {
            return connectedAccount.venmo.map((venmoUser, index) => (
                <tr key={`venmo-${venmoUser}-${index}`}>
                    <td>Venmo - {venmoUser}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>
            ));
        }

        // Handle Splitwise data (array)
        if (connectedAccount.splitwise) {
            return connectedAccount.splitwise.map((splitwiseUser, index) => (
                <tr key={`splitwise-${splitwiseUser}-${index}`}>
                    <td>Splitwise - {splitwiseUser}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>
            ));
        }

        // Handle Stripe data (array of objects)
        if (connectedAccount.stripe) {
            return connectedAccount.stripe.map((stripeAccount) => {
                const { institution_name, display_name, last4, _id, status } = stripeAccount;
                return (
                    <tr key={`stripe-${_id}`}>
                        <td>{institution_name} {display_name} {last4}</td>
                        {status === 'inactive' ?
                            <td><Button onClick={() => { relinkAccount(_id) }} variant="secondary">Reactivate</Button></td>
                            : <td>Active</td>}
                        <td>{accountsAndBalances[_id] && formatBalance(accountsAndBalances[_id]["balance"])}</td>
                        <td>{accountsAndBalances[_id] && formatDate(accountsAndBalances[_id]["as_of"])}</td>
                    </tr>
                );
            });
        }

        return null;
    };

    const renderStripeAccount = (stripeAccount) => {
        return (
            <tr key={stripeAccount.id}>
                <td>{stripeAccount.institution_name} {stripeAccount.subcategory} ({stripeAccount.id})</td>
                <td><Button onClick={() => { relinkAccount(stripeAccount.id) }} variant="secondary">Reactivate</Button></td>
                <td>{accountsAndBalances[stripeAccount.id] && formatDate(accountsAndBalances[stripeAccount.id]["as_of"])}</td>
            </tr>
        )
    }

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
                            <th>Status</th>
                            <th>Balance</th>
                            <th>Last Updated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {connectedAccounts.length > 0 ?
                            connectedAccounts.flatMap(renderConnectedAccount)
                            :
                            // @ts-expect-error TODO: Need to look into this type error
                            <tr align="center"><td colSpan="4">
                                No connected accounts found
                            </td></tr>
                        }
                    </tbody>
                </Table>
                <br />
                <h4>Net Worth: {formatBalance(netWorth)}</h4>
                <br />
                <h4>Inactive Accounts</h4>
                <Table striped bordered hover>
                    <thead>
                        <tr>
                            <th>Connected Accounts</th>
                            <th>Reactivate</th>
                            <th>Last Updated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {connectedAccounts.length > 0 ?
                            connectedAccounts.find(account => account.stripe)?.stripe.filter(account => account.status === "inactive").flatMap(renderStripeAccount)
                            :
                            // @ts-expect-error TODO: Need to look into this type error
                            <tr align="center"><td colSpan="4">
                                No inactive connected accounts found
                            </td></tr>
                        }
                    </tbody>
                </Table>
            </div>
        </>
    )
}