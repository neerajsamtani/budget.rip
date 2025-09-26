import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Elements } from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import { Stripe } from "@stripe/stripe-js/types/stripe-js";
import React, { Fragment, useEffect, useState } from "react";
import { toast } from "sonner";
import FinancialConnectionsForm from "../components/FinancialConnectionsForm";
import axiosInstance from "../utils/axiosInstance";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";

export default function ConnectedAccountsPage({ stripePromise }: { stripePromise: Promise<Stripe | null> }) {

    const [connectedAccounts, setConnectedAccounts] = useState([])
    const [accountsAndBalances, setAccountsAndBalances] = useState({})
    const [clientSecret, setClientSecret] = useState("");
    const [stripeAccounts, setStripeAccounts] = useState<FinancialConnectionsSession.Account[]>([])

    const formatDate = (unixTime: number) => DateFormatter.format(new Date(unixTime * 1000))

    let netWorth = 0;
    // Only active accounts are included in the net worth calculation
    Object.keys(accountsAndBalances).forEach(key => {
        if (accountsAndBalances[key]["status"] === "active") {
            netWorth += accountsAndBalances[key]["balance"]
        }
    })

    const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);

    useEffect(() => {
        const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
        axiosInstance.get(`${VITE_API_ENDPOINT}api/connected_accounts`)
            .then(response => {
                setConnectedAccounts(response.data)
            })
            .catch(error => console.log(error));
        axiosInstance.get(`${VITE_API_ENDPOINT}api/accounts_and_balances`)
            .then(response => {
                setAccountsAndBalances(response.data)
            })
            .catch(error => console.log(error));
    }, [])

    const createSession = () => {
        axiosInstance.post(`${VITE_API_ENDPOINT}api/create-fc-session`)
            .then(response => setClientSecret(response.data.clientSecret))
            .catch(error => console.log(error));
    }

    const subscribeToAccounts = () => {
        if (stripeAccounts) {
            for (const account of stripeAccounts) {
                axiosInstance.get(`${VITE_API_ENDPOINT}api/subscribe_to_account/${account.id}`)
                    .then(response => console.log(response.data))
            }
        }
        setClientSecret("")
        setStripeAccounts([])
        toast.info("Notification", {
            description: "Subscribing to the accounts provided. Please refresh the page.",
            duration: 3500,
        });
    }

    const relinkAccount = (accountId) => {
        axiosInstance.get(`${VITE_API_ENDPOINT}api/relink_account/${accountId}`)
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
                <TableRow key={`venmo-${venmoUser}-${index}`}>
                    <TableCell>Venmo - {venmoUser}</TableCell>
                    <TableCell></TableCell>
                    <TableCell></TableCell>
                    <TableCell></TableCell>
                </TableRow>
            ));
        }

        // Handle Splitwise data (array)
        if (connectedAccount.splitwise) {
            return connectedAccount.splitwise.map((splitwiseUser, index) => (
                <TableRow key={`splitwise-${splitwiseUser}-${index}`}>
                    <TableCell>Splitwise - {splitwiseUser}</TableCell>
                    <TableCell></TableCell>
                    <TableCell></TableCell>
                    <TableCell></TableCell>
                </TableRow>
            ));
        }

        // Handle Stripe data (array of objects)
        if (connectedAccount.stripe) {
            return connectedAccount.stripe.map((stripeAccount) => {
                const { institution_name, display_name, last4, _id, status } = stripeAccount;
                return (
                    <TableRow key={`stripe-${_id}`}>
                        <TableCell>{institution_name} {display_name} {last4}</TableCell>
                        {status === 'inactive' ?
                            <TableCell><Button onClick={() => { relinkAccount(_id) }} variant="secondary">Reactivate</Button></TableCell>
                            : <TableCell>Active</TableCell>}
                        <TableCell>{accountsAndBalances[_id] && CurrencyFormatter.format(accountsAndBalances[_id]["balance"])}</TableCell>
                        <TableCell>{accountsAndBalances[_id] && formatDate(accountsAndBalances[_id]["as_of"])}</TableCell>
                    </TableRow>
                );
            });
        }

        return null;
    };

    const renderStripeAccount = (stripeAccount) => {
        return (
            <TableRow key={stripeAccount.id}>
                <TableCell>{stripeAccount.institution_name} {stripeAccount.subcategory} ({stripeAccount.id})</TableCell>
                <TableCell><Button onClick={() => { relinkAccount(stripeAccount.id) }} variant="secondary">Reactivate</Button></TableCell>
                <TableCell>{accountsAndBalances[stripeAccount.id] && formatDate(accountsAndBalances[stripeAccount.id]["as_of"])}</TableCell>
            </TableRow>
        )
    }

    return (
        <>
            <div>
                <h1>Connected Accounts</h1>
                <div className="Form">
                    {clientSecret ?
                        stripeAccounts.length > 0 ?
                            <Fragment>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Bank Accounts Received:</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {
                                            stripeAccounts
                                                .map(account => (
                                                    <TableRow key={account.id}>
                                                        <TableCell>
                                                            {account.institution_name} {account.subcategory} ({account.id})
                                                        </TableCell>
                                                    </TableRow>
                                                ))
                                        }
                                    </TableBody>
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
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Connected Accounts</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Balance</TableHead>
                            <TableHead>Last Updated</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {connectedAccounts.length > 0 ?
                            connectedAccounts.flatMap(renderConnectedAccount)
                            :
                            <TableRow>
                                <TableCell colSpan={4} className="text-center">
                                    No connected accounts found
                                </TableCell>
                            </TableRow>
                        }
                    </TableBody>
                </Table>
                <br />
                <h4>Net Worth: {CurrencyFormatter.format(netWorth)}</h4>
                <br />
                <h4>Inactive Accounts</h4>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Connected Accounts</TableHead>
                            <TableHead>Reactivate</TableHead>
                            <TableHead>Last Updated</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {connectedAccounts.length > 0 ?
                            connectedAccounts.find(account => account.stripe)?.stripe.filter(account => account.status === "inactive").flatMap(renderStripeAccount)
                            :
                            <TableRow>
                                <TableCell colSpan={3} className="text-center">
                                    No inactive connected accounts found
                                </TableCell>
                            </TableRow>
                        }
                    </TableBody>
                </Table>
            </div>
        </>
    )
}