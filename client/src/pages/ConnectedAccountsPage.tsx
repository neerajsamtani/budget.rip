import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Elements } from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import { Stripe } from "@stripe/stripe-js/types/stripe-js";
import React, { useState } from "react";
import { toast } from "sonner";
import FinancialConnectionsForm from "../components/FinancialConnectionsForm";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { StatusBadge } from "../components/ui/status-badge";
import { Body, H1, H4 } from "../components/ui/typography";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { useConnectedAccounts, useAccountsAndBalances, useCreateFinancialConnectionsSession, useSubscribeToAccount, useRelinkAccount } from "../hooks/useApi";

export default function ConnectedAccountsPage({ stripePromise }: { stripePromise: Promise<Stripe | null> }) {
    const [clientSecret, setClientSecret] = useState("");
    const [stripeAccounts, setStripeAccounts] = useState<FinancialConnectionsSession.Account[]>([])

    const { data: connectedAccounts = [] } = useConnectedAccounts()
    const { data: accountsAndBalances = {} } = useAccountsAndBalances()
    const createSessionMutation = useCreateFinancialConnectionsSession()
    const subscribeToAccountMutation = useSubscribeToAccount()
    const relinkAccountMutation = useRelinkAccount()

    const formatDate = (unixTime: number) => DateFormatter.format(new Date(unixTime * 1000))

    let netWorth = 0;
    // Only active accounts are included in the net worth calculation
    Object.keys(accountsAndBalances).forEach(key => {
        if (accountsAndBalances[key]["status"] === "active") {
            netWorth += accountsAndBalances[key]["balance"]
        }
    })

    const createSession = () => {
        createSessionMutation.mutate(undefined, {
            onSuccess: (secret) => setClientSecret(secret),
            onError: (error: Error) => {
                toast.error("Error", {
                    description: error.message || "Failed to create session",
                    duration: 3500,
                });
            }
        })
    }

    const subscribeToAccounts = () => {
        if (stripeAccounts) {
            for (const account of stripeAccounts) {
                subscribeToAccountMutation.mutate(account.id, {
                    onSuccess: () => toast.info("Notification", {
                        description: `Subscribed to the account ${account.id}`,
                        duration: 3500,
                    }),
                    onError: (error: Error) => {
                        toast.error("Error", {
                            description: error.message || `Failed to subscribe to account ${account.id}`,
                            duration: 3500,
                        });
                    }
                })
            }
        }
        setClientSecret("")
        setStripeAccounts([])
        toast.info("Notification", {
            description: "Subscribing to the accounts provided. Data will refresh automatically.",
            duration: 3500,
        });
    }

    const relinkAccount = (accountId: string) => {
        relinkAccountMutation.mutate(accountId, {
            onSuccess: (secret) => setClientSecret(secret),
            onError: (error: Error) => {
                toast.error("Error", {
                    description: error.message || "Failed to relink account",
                    duration: 3500,
                });
            }
        })
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
                const { institution_name, display_name, last4, id, status } = stripeAccount;
                return (
                    <TableRow key={`stripe-${id}`}>
                        <TableCell>{institution_name} {display_name} {last4}</TableCell>
                        {status === 'inactive' ?
                            <TableCell><Button onClick={() => { relinkAccount(id) }} variant="secondary">Reactivate</Button></TableCell>
                            : <TableCell>Active</TableCell>}
                        <TableCell>
                            {accountsAndBalances[id] && (
                                <StatusBadge status={accountsAndBalances[id]["balance"] >= 0 ? 'success' : 'error'}>
                                    {CurrencyFormatter.format(accountsAndBalances[id]["balance"])}
                                </StatusBadge>
                            )}
                        </TableCell>
                        <TableCell>{accountsAndBalances[id] && formatDate(accountsAndBalances[id]["as_of"])}</TableCell>
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
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {connectedAccounts.length > 0 ? (
                                connectedAccounts.flatMap(renderConnectedAccount)
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={4} className="text-center text-muted-foreground">
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