import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Elements } from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import { Stripe } from "@stripe/stripe-js/types/stripe-js";
import React, { useContext, useEffect, useState } from "react";
import { toast } from "sonner";
import FinancialConnectionsForm from "../components/FinancialConnectionsForm";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { StatusBadge } from "../components/ui/status-badge";
import { Body, H1, H4 } from "../components/ui/typography";
import axiosInstance from "../utils/axiosInstance";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { showErrorToast, showSuccessToast } from "../utils/toast-helpers";
import { LineItemsContext } from "../contexts/LineItemsContext";

export default function ConnectedAccountsPage({ stripePromise }: { stripePromise: Promise<Stripe | null> }) {

    const [connectedAccounts, setConnectedAccounts] = useState([])
    const [accountsAndBalances, setAccountsAndBalances] = useState({})
    const [clientSecret, setClientSecret] = useState("");
    const [stripeAccounts, setStripeAccounts] = useState<FinancialConnectionsSession.Account[]>([])
    const [refreshingAccounts, setRefreshingAccounts] = useState<Set<string>>(new Set());

    const { dispatch: lineItemsDispatch } = useContext(LineItemsContext);

    const formatDate = (unixTime: number) => DateFormatter.format(new Date(unixTime * 1000))

    let netWorth = 0;
    // Only active accounts are included in the net worth calculation
    Object.keys(accountsAndBalances).forEach(key => {
        if (accountsAndBalances[key]["status"] === "active") {
            netWorth += accountsAndBalances[key]["balance"]
        }
    })


    useEffect(() => {
        axiosInstance.get(`api/connected_accounts`)
            .then(response => {
                setConnectedAccounts(response.data)
            })
            .catch(showErrorToast);
        axiosInstance.get(`api/accounts_and_balances`)
            .then(response => {
                setAccountsAndBalances(response.data)
            })
            .catch(showErrorToast);
    }, [])

    const createSession = () => {
        axiosInstance.post(`api/create-fc-session`)
            .then(response => setClientSecret(response.data.clientSecret))
            .catch(showErrorToast);
    }

    const subscribeToAccounts = () => {
        if (stripeAccounts) {
            for (const account of stripeAccounts) {
                axiosInstance.get(`api/subscribe_to_account/${account.id}`)
                    .then(() => toast.info("Notification", {
                        description: `Subscribed to the account ${account.id}`,
                        duration: 3500,
                    }))
                    .catch(showErrorToast);
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
        axiosInstance.get(`api/relink_account/${accountId}`)
            .then(response => setClientSecret(response.data.clientSecret))
            .catch(showErrorToast);
    }

    const handleRefreshAccount = (accountType: string, accountId?: string) => {
        const refreshKey = accountId || accountType;
        setRefreshingAccounts(prev => new Set(prev).add(refreshKey));

        const url = accountId
            ? `api/account/${accountType}/${accountId}/refresh`
            : `api/account/${accountType}/refresh`;

        axiosInstance.get(url)
            .then(response => {
                showSuccessToast(`Refreshed ${accountType} account`, "Notification");
                lineItemsDispatch({
                    type: "populate_line_items",
                    fetchedLineItems: response.data.data
                });
                // Refresh balances after updating transactions
                axiosInstance.get(`api/accounts_and_balances`)
                    .then(response => {
                        setAccountsAndBalances(response.data);
                    })
                    .catch(showErrorToast);
            })
            .catch((error) => {
                showErrorToast(new Error(`Error refreshing ${accountType} account`), "Notification");
            })
            .finally(() => {
                setRefreshingAccounts(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(refreshKey);
                    return newSet;
                });
            });
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
                    <TableCell>
                        <Button
                            onClick={() => handleRefreshAccount("venmo")}
                            variant="outline"
                            size="sm"
                            disabled={refreshingAccounts.has("venmo")}
                        >
                            {refreshingAccounts.has("venmo") ? "Refreshing..." : "Refresh"}
                        </Button>
                    </TableCell>
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
                    <TableCell>
                        <Button
                            onClick={() => handleRefreshAccount("splitwise")}
                            variant="outline"
                            size="sm"
                            disabled={refreshingAccounts.has("splitwise")}
                        >
                            {refreshingAccounts.has("splitwise") ? "Refreshing..." : "Refresh"}
                        </Button>
                    </TableCell>
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
                        <TableCell>
                            {accountsAndBalances[_id] && (
                                <StatusBadge status={accountsAndBalances[_id]["balance"] >= 0 ? 'success' : 'error'}>
                                    {CurrencyFormatter.format(accountsAndBalances[_id]["balance"])}
                                </StatusBadge>
                            )}
                        </TableCell>
                        <TableCell>{accountsAndBalances[_id] && formatDate(accountsAndBalances[_id]["as_of"])}</TableCell>
                        <TableCell>
                            <Button
                                onClick={() => handleRefreshAccount("stripe", _id)}
                                variant="outline"
                                size="sm"
                                disabled={refreshingAccounts.has(_id)}
                            >
                                {refreshingAccounts.has(_id) ? "Refreshing..." : "Refresh"}
                            </Button>
                        </TableCell>
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
        <PageContainer>
            <PageHeader>
                <H1>Connected Accounts</H1>
                <Body className="text-muted-foreground">
                    Manage your linked financial accounts and view balances
                </Body>
            </PageHeader>

            <div className="space-y-8">
                <div className="space-y-4">
                    {clientSecret ? (
                        stripeAccounts.length > 0 ? (
                            <div className="space-y-4">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Bank Accounts Received:</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {stripeAccounts.map(account => (
                                            <TableRow key={account.id}>
                                                <TableCell>
                                                    {account.institution_name} {account.subcategory} ({account.id})
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                                <Button onClick={subscribeToAccounts}>
                                    Subscribe to these accounts
                                </Button>
                            </div>
                        ) : (
                            <Elements options={options} stripe={stripePromise}>
                                <FinancialConnectionsForm fcsess_secret={clientSecret} setStripeAccounts={setStripeAccounts} />
                            </Elements>
                        )
                    ) : (
                        <Button onClick={createSession}>
                            Connect A New Account
                        </Button>
                    )}
                </div>

                <div className="space-y-6">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Connected Accounts</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Balance</TableHead>
                                <TableHead>Last Updated</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {connectedAccounts.length > 0 ? (
                                connectedAccounts.flatMap(renderConnectedAccount)
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                                        No connected accounts found
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>

                    <div className="bg-muted rounded-lg p-4 md:p-6">
                        <H4>Net Worth: <StatusBadge status={netWorth >= 0 ? 'success' : 'error'}>{CurrencyFormatter.format(netWorth)}</StatusBadge></H4>
                    </div>

                    <div className="space-y-4">
                        <H4>Inactive Accounts</H4>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Connected Accounts</TableHead>
                                    <TableHead>Reactivate</TableHead>
                                    <TableHead>Last Updated</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {connectedAccounts.length > 0 ? (
                                    connectedAccounts.find(account => account.stripe)?.stripe.filter(account => account.status === "inactive").flatMap(renderStripeAccount)
                                ) : (
                                    <TableRow>
                                        <TableCell colSpan={3} className="text-center text-muted-foreground">
                                            No inactive connected accounts found
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}