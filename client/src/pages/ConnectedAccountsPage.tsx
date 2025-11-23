import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Elements } from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import { Stripe } from "@stripe/stripe-js/types/stripe-js";
import React, { useState } from "react";
import { toast } from "sonner";
import { RefreshCw, Wallet } from "lucide-react";
import FinancialConnectionsForm from "../components/FinancialConnectionsForm";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { StatusBadge } from "../components/ui/status-badge";
import { Body, H1, H4 } from "../components/ui/typography";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { useConnectedAccounts, useAccountsAndBalances, useCreateFinancialConnectionsSession, useSubscribeToAccount, useRelinkAccount, useRefreshAccount } from "../hooks/useApi";

export default function ConnectedAccountsPage({ stripePromise }: { stripePromise: Promise<Stripe | null> }) {
    const [clientSecret, setClientSecret] = useState("");
    const [stripeAccounts, setStripeAccounts] = useState<FinancialConnectionsSession.Account[]>([])
    const [refreshingAccountId, setRefreshingAccountId] = useState<string | null>(null)

    const { data: connectedAccounts = [] } = useConnectedAccounts()
    const { data: accountsAndBalances = {} } = useAccountsAndBalances()
    const createSessionMutation = useCreateFinancialConnectionsSession()
    const subscribeToAccountMutation = useSubscribeToAccount()
    const relinkAccountMutation = useRelinkAccount()
    const refreshAccountMutation = useRefreshAccount()

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

    const refreshAccount = (accountId: string, source: 'stripe' | 'venmo' | 'splitwise') => {
        setRefreshingAccountId(accountId)
        refreshAccountMutation.mutate({ accountId, source }, {
            onSuccess: () => {
                toast.success("Success", {
                    description: "Account data refreshed successfully",
                    duration: 3500,
                });
                setRefreshingAccountId(null)
            },
            onError: (error: Error) => {
                toast.error("Error", {
                    description: error.message || "Failed to refresh account",
                    duration: 3500,
                });
                setRefreshingAccountId(null)
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

    const AccountNameWithTooltip = ({ name, id }) => (
        <Tooltip>
            <TooltipTrigger asChild>
                <span>{name}</span>
            </TooltipTrigger>
            <TooltipContent>
                Account ID: {id}
            </TooltipContent>
        </Tooltip>
    );

    const renderConnectedAccount = (connectedAccount) => {
        // Handle Venmo data (array)
        if (connectedAccount.venmo) {
            return connectedAccount.venmo.map((venmoUser, index) => {
                const accountKey = `venmo-${venmoUser}`;
                return (
                    <TableRow key={`${accountKey}-${index}`}>
                        <TableCell>Venmo - {venmoUser}</TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                        <TableCell>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => refreshAccount(accountKey, 'venmo')}
                                disabled={refreshingAccountId === accountKey}
                            >
                                <RefreshCw className={`h-4 w-4 ${refreshingAccountId === accountKey ? 'animate-spin' : ''}`} />
                            </Button>
                        </TableCell>
                    </TableRow>
                );
            });
        }

        // Handle Splitwise data (array)
        if (connectedAccount.splitwise) {
            return connectedAccount.splitwise.map((splitwiseUser, index) => {
                const accountKey = `splitwise-${splitwiseUser}`;
                return (
                    <TableRow key={`${accountKey}-${index}`}>
                        <TableCell>Splitwise - {splitwiseUser}</TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                        <TableCell>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => refreshAccount(accountKey, 'splitwise')}
                                disabled={refreshingAccountId === accountKey}
                            >
                                <RefreshCw className={`h-4 w-4 ${refreshingAccountId === accountKey ? 'animate-spin' : ''}`} />
                            </Button>
                        </TableCell>
                    </TableRow>
                );
            });
        }

        // Handle Stripe data (array of objects)
        if (connectedAccount.stripe) {
            return connectedAccount.stripe
                // Filter: only show active accounts OR inactive accounts that can be relinked
                .filter((stripeAccount) => {
                    const { status } = stripeAccount;
                    const canRelink = accountsAndBalances[stripeAccount.id]?.can_relink ?? false;
                    return status === 'active' || (status === 'inactive' && canRelink);
                })
                .map((stripeAccount) => {
                    const { institution_name, display_name, last4, id, status } = stripeAccount;
                    const canRelink = accountsAndBalances[id]?.can_relink ?? false;
                    return (
                        <TableRow key={`stripe-${id}`}>
                            <TableCell>
                                <AccountNameWithTooltip
                                    name={`${institution_name} ${display_name} ${last4}`}
                                    id={id}
                                />
                            </TableCell>
                            {status === 'inactive' && canRelink ?
                                <TableCell><Button onClick={() => { relinkAccount(id) }} variant="secondary">Reactivate</Button></TableCell>
                                : <TableCell>Active</TableCell>}
                            <TableCell>
                                {accountsAndBalances[id]?.balance != null ? (
                                    <StatusBadge status={accountsAndBalances[id]["balance"] >= 0 ? 'success' : 'error'}>
                                        {CurrencyFormatter.format(accountsAndBalances[id]["balance"])}
                                    </StatusBadge>
                                ) : (
                                    <span className="text-muted-foreground text-sm">—</span>
                                )}
                            </TableCell>
                            <TableCell>
                                {accountsAndBalances[id]?.as_of ? (
                                    formatDate(accountsAndBalances[id]["as_of"])
                                ) : (
                                    <span className="text-muted-foreground text-sm">—</span>
                                )}
                            </TableCell>
                            <TableCell>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => refreshAccount(id, 'stripe')}
                                    disabled={refreshingAccountId === id || status === 'inactive'}
                                >
                                    <RefreshCw className={`h-4 w-4 ${refreshingAccountId === id ? 'animate-spin' : ''}`} />
                                </Button>
                            </TableCell>
                        </TableRow>
                    );
                });
        }

        return null;
    };

    const renderStripeAccount = (stripeAccount) => {
        const canRelink = accountsAndBalances[stripeAccount.id]?.can_relink ?? false;
        return (
            <TableRow key={stripeAccount.id}>
                <TableCell>
                    <AccountNameWithTooltip
                        name={`${stripeAccount.institution_name} ${stripeAccount.display_name} ${stripeAccount.last4}`}
                        id={stripeAccount.id}
                    />
                </TableCell>
                <TableCell>
                    {canRelink ? (
                        <Button onClick={() => { relinkAccount(stripeAccount.id) }} variant="secondary">Reactivate</Button>
                    ) : (
                        <span className="text-muted-foreground text-sm">Cannot relink</span>
                    )}
                </TableCell>
                <TableCell>
                    {accountsAndBalances[stripeAccount.id]?.as_of ? (
                        formatDate(accountsAndBalances[stripeAccount.id]["as_of"])
                    ) : (
                        <span className="text-muted-foreground text-sm">—</span>
                    )}
                </TableCell>
            </TableRow>
        )
    }

    // Mobile card component for connected accounts
    const AccountCard = ({ name, id, status, balance, lastUpdated, onRefresh, onRelink, isRefreshing, canRelink }: {
        name: string;
        id: string;
        status?: 'active' | 'inactive';
        balance?: number | null;
        lastUpdated?: string | null;
        onRefresh?: () => void;
        onRelink?: () => void;
        isRefreshing?: boolean;
        canRelink?: boolean;
    }) => (
        <div className="p-4 border-b last:border-b-0">
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="p-2 bg-muted rounded-lg shrink-0">
                        <Wallet className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="min-w-0 flex-1">
                        <p className="font-medium text-foreground truncate" title={name}>{name}</p>
                        {(status || balance != null) && (
                            <div className="flex flex-wrap items-center gap-2 mt-1">
                                {status === 'inactive' && canRelink ? (
                                    <Button onClick={onRelink} variant="secondary" size="sm">Reactivate</Button>
                                ) : status && (
                                    <span className="text-sm text-muted-foreground capitalize">{status}</span>
                                )}
                                {balance != null && (
                                    <StatusBadge status={balance >= 0 ? 'success' : 'error'}>
                                        {CurrencyFormatter.format(balance)}
                                    </StatusBadge>
                                )}
                            </div>
                        )}
                        {lastUpdated && (
                            <p className="text-xs text-muted-foreground mt-1">{lastUpdated}</p>
                        )}
                    </div>
                </div>
                {onRefresh && (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onRefresh}
                        disabled={isRefreshing || status === 'inactive'}
                        className="shrink-0"
                    >
                        <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                    </Button>
                )}
            </div>
        </div>
    );

    const renderConnectedAccountCards = (connectedAccount) => {
        if (connectedAccount.venmo) {
            return connectedAccount.venmo.map((venmoUser, index) => {
                const accountKey = `venmo-${venmoUser}`;
                return (
                    <AccountCard
                        key={`${accountKey}-${index}`}
                        name={`Venmo - ${venmoUser}`}
                        id={accountKey}
                        onRefresh={() => refreshAccount(accountKey, 'venmo')}
                        isRefreshing={refreshingAccountId === accountKey}
                    />
                );
            });
        }

        if (connectedAccount.splitwise) {
            return connectedAccount.splitwise.map((splitwiseUser, index) => {
                const accountKey = `splitwise-${splitwiseUser}`;
                return (
                    <AccountCard
                        key={`${accountKey}-${index}`}
                        name={`Splitwise - ${splitwiseUser}`}
                        id={accountKey}
                        onRefresh={() => refreshAccount(accountKey, 'splitwise')}
                        isRefreshing={refreshingAccountId === accountKey}
                    />
                );
            });
        }

        if (connectedAccount.stripe) {
            return connectedAccount.stripe
                .filter((stripeAccount) => {
                    const { status } = stripeAccount;
                    const canRelink = accountsAndBalances[stripeAccount.id]?.can_relink ?? false;
                    return status === 'active' || (status === 'inactive' && canRelink);
                })
                .map((stripeAccount) => {
                    const { institution_name, display_name, last4, id, status } = stripeAccount;
                    const canRelink = accountsAndBalances[id]?.can_relink ?? false;
                    return (
                        <AccountCard
                            key={`stripe-${id}`}
                            name={`${institution_name} ${display_name} ${last4}`}
                            id={id}
                            status={status}
                            balance={accountsAndBalances[id]?.balance}
                            lastUpdated={accountsAndBalances[id]?.as_of ? formatDate(accountsAndBalances[id]["as_of"]) : null}
                            onRefresh={() => refreshAccount(id, 'stripe')}
                            onRelink={() => relinkAccount(id)}
                            isRefreshing={refreshingAccountId === id}
                            canRelink={canRelink}
                        />
                    );
                });
        }

        return null;
    };

    const renderInactiveAccountCard = (stripeAccount) => {
        const canRelink = accountsAndBalances[stripeAccount.id]?.can_relink ?? false;
        return (
            <AccountCard
                key={stripeAccount.id}
                name={`${stripeAccount.institution_name} ${stripeAccount.display_name} ${stripeAccount.last4}`}
                id={stripeAccount.id}
                status="inactive"
                lastUpdated={accountsAndBalances[stripeAccount.id]?.as_of ? formatDate(accountsAndBalances[stripeAccount.id]["as_of"]) : null}
                onRelink={canRelink ? () => relinkAccount(stripeAccount.id) : undefined}
                canRelink={canRelink}
            />
        );
    };

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
                    {/* Mobile card layout */}
                    <div className="md:hidden">
                        {connectedAccounts.length > 0 ? (
                            <div className="rounded-xl bg-white shadow-sm border overflow-hidden">
                                {connectedAccounts.flatMap(renderConnectedAccountCards)}
                            </div>
                        ) : (
                            <Body className="text-center text-muted-foreground py-4">
                                No connected accounts found
                            </Body>
                        )}
                    </div>

                    {/* Desktop table layout */}
                    <div className="hidden md:block">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Connected Accounts</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Balance</TableHead>
                                    <TableHead>Last Updated</TableHead>
                                    <TableHead>Refresh</TableHead>
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
                    </div>

                    <div className="bg-muted rounded-lg p-4 md:p-6">
                        <H4>Net Worth: <StatusBadge status={netWorth >= 0 ? 'success' : 'error'}>{CurrencyFormatter.format(netWorth)}</StatusBadge></H4>
                    </div>

                    <div className="space-y-4">
                        <H4>Inactive Accounts</H4>

                        {/* Mobile card layout */}
                        <div className="md:hidden">
                            {connectedAccounts.find(account => account.stripe)?.stripe.filter(account => account.status === "inactive").length > 0 ? (
                                <div className="rounded-xl bg-white shadow-sm border overflow-hidden">
                                    {connectedAccounts.find(account => account.stripe)?.stripe.filter(account => account.status === "inactive").map(renderInactiveAccountCard)}
                                </div>
                            ) : (
                                <Body className="text-center text-muted-foreground py-4">
                                    No inactive accounts
                                </Body>
                            )}
                        </div>

                        {/* Desktop table layout */}
                        <div className="hidden md:block">
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
            </div>
        </PageContainer>
    )
}