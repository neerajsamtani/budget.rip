import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Elements } from "@stripe/react-stripe-js";
import { FinancialConnectionsSession } from "@stripe/stripe-js/types/api";
import { Stripe } from "@stripe/stripe-js/types/stripe-js";
import { RefreshCw } from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";
import FinancialConnectionsForm from "../components/FinancialConnectionsForm";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { StatusBadge } from "../components/ui/status-badge";
import { Body, H1, H4 } from "../components/ui/typography";
import { ConnectedAccount, StripeAccount, useAccountsAndBalances, useConnectedAccounts, useCreateFinancialConnectionsSession, useRefreshAccount, useRelinkAccount, useSubscribeToAccount } from "../hooks/useApi";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";

const BALANCE_OUTDATED_AFTER_DAYS = 7;
const DAY_IN_MILLISECONDS = 24 * 60 * 60 * 1000;

export default function ConnectedAccountsPage({ stripePromise }: { stripePromise: Promise<Stripe | null> }) {
    const [clientSecret, setClientSecret] = useState("");
    const [stripeAccounts, setStripeAccounts] = useState<FinancialConnectionsSession.Account[]>([])
    const [refreshingAccountId, setRefreshingAccountId] = useState<string | null>(null)

    const {
        data: connectedAccounts,
        isLoading: isLoadingAccounts,
        isError: isAccountsError,
        refetch: refetchAccounts,
    } = useConnectedAccounts()
    const accounts = connectedAccounts ?? []
    const stripeConnectedAccounts = accounts.find(account => account.stripe)?.stripe ?? []
    const activeStripeAccounts = stripeConnectedAccounts.filter(account => account.status === "active")
    const inactiveAccounts = stripeConnectedAccounts.filter(account => account.status === "inactive")
    const activeAccounts = [
        ...accounts.filter(account => account.venmo?.length || account.splitwise?.length),
        ...(activeStripeAccounts.length > 0 ? [{ stripe: activeStripeAccounts }] : []),
    ]
    const {
        data: accountsAndBalances,
        isLoading: isLoadingBalances,
        isError: isBalancesError,
        refetch: refetchBalances,
    } = useAccountsAndBalances()
    const balances = accountsAndBalances ?? {}
    const createSessionMutation = useCreateFinancialConnectionsSession()
    const subscribeToAccountMutation = useSubscribeToAccount()
    const relinkAccountMutation = useRelinkAccount()
    const refreshAccountMutation = useRefreshAccount()

    const isLoading = isLoadingAccounts || isLoadingBalances

    const formatDate = (unixTime: number) => DateFormatter.format(new Date(unixTime * 1000))

    const formatAge = (unixTime: number) => {
        const ageInDays = Math.floor(Math.max(0, Date.now() - unixTime * 1000) / DAY_IN_MILLISECONDS)
        if (ageInDays === 0) return "today"
        if (ageInDays === 1) return "1 day ago"
        return `${ageInDays} days ago`
    }

    // The tables carry a "Last Updated" header; the mobile cards have none, so they label the date.
    const renderBalanceFreshness = (asOf?: number | null, showLabel = false) => {
        if (asOf == null) {
            return <span className="text-muted-foreground text-sm">{showLabel ? "Balance updated: Not available" : "Not available"}</span>
        }

        const isOutdated = Date.now() - asOf * 1000 > BALANCE_OUTDATED_AFTER_DAYS * DAY_IN_MILLISECONDS
        return (
            <div className="space-y-0.5">
                <div>{showLabel ? "Balance updated " : ""}{formatDate(asOf)} ({formatAge(asOf)})</div>
                {isOutdated && (
                    <div className="text-amber-700 text-xs">Balance may be outdated</div>
                )}
            </div>
        )
    }

    const renderBalance = (balance?: number | null) => balance != null ? (
        <StatusBadge status={balance >= 0 ? 'success' : 'error'}>
            {CurrencyFormatter.format(balance)}
        </StatusBadge>
    ) : (
        <span className="text-muted-foreground text-sm">Not available</span>
    )

    const activeBalanceEntries = Object.values(balances).filter(account => account.status === "active")
    const hasMissingActiveBalance = activeBalanceEntries.some(account => (
        typeof account.balance !== "number" || !Number.isFinite(account.balance)
    )) || activeStripeAccounts.some(account => {
        const balance = balances[account.id]?.balance
        return typeof balance !== "number" || !Number.isFinite(balance)
    })
    const hasNetWorth = accountsAndBalances !== undefined && !isLoadingBalances && !hasMissingActiveBalance
    const netWorth = hasNetWorth
        ? activeBalanceEntries.reduce((total, account) => total + account.balance, 0)
        : null

    const hasQueryError = isAccountsError || isBalancesError
    const retryQueries = () => {
        void Promise.all([refetchAccounts(), refetchBalances()])
    }

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

    const AccountNameWithTooltip = ({ name, id }: { name: string; id: string }) => (
        <Tooltip>
            <TooltipTrigger asChild>
                <span>{name}</span>
            </TooltipTrigger>
            <TooltipContent>
                Account ID: {id}
            </TooltipContent>
        </Tooltip>
    );

    const renderConnectedAccount = (connectedAccount: ConnectedAccount) => {
        // Handle Venmo data (array)
        if (connectedAccount.venmo) {
            return connectedAccount.venmo.map((venmoUser, index) => {
                const accountKey = `venmo-${venmoUser}`;
                return (
                    <TableRow key={`${accountKey}-${index}`}>
                        <TableCell>Venmo - {venmoUser}</TableCell>
                        <TableCell>Connected</TableCell>
                        <TableCell>{renderBalance()}</TableCell>
                        <TableCell>{renderBalanceFreshness()}</TableCell>
                        <TableCell>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => refreshAccount(accountKey, 'venmo')}
                                disabled={refreshingAccountId === accountKey}
                                aria-label={`Refresh Venmo - ${venmoUser} account data`}
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
                        <TableCell>Connected</TableCell>
                        <TableCell>{renderBalance()}</TableCell>
                        <TableCell>{renderBalanceFreshness()}</TableCell>
                        <TableCell>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => refreshAccount(accountKey, 'splitwise')}
                                disabled={refreshingAccountId === accountKey}
                                aria-label={`Refresh Splitwise - ${splitwiseUser} account data`}
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
                    const canRelink = balances[stripeAccount.id]?.can_relink ?? false;
                    return status === 'active' || (status === 'inactive' && canRelink);
                })
                .map((stripeAccount) => {
                    const { institution_name, display_name, last4, id, status } = stripeAccount;
                    const canRelink = balances[id]?.can_relink ?? false;
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
                                {renderBalance(balances[id]?.balance)}
                            </TableCell>
                            <TableCell>
                                {renderBalanceFreshness(balances[id]?.as_of)}
                            </TableCell>
                            <TableCell>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => refreshAccount(id, 'stripe')}
                                    disabled={refreshingAccountId === id || status === 'inactive'}
                                    aria-label={`Refresh ${institution_name} ${display_name} ${last4} account data`}
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

    const renderStripeAccount = (stripeAccount: StripeAccount) => {
        const canRelink = balances[stripeAccount.id]?.can_relink ?? false;
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
                    {renderBalanceFreshness(balances[stripeAccount.id]?.as_of)}
                </TableCell>
            </TableRow>
        )
    }

    // Mobile card component for connected accounts
    const AccountCard = ({ name, status, balance, balanceAsOf, onRefresh, onRelink, isRefreshing, canRelink }: {
        name: string;
        status?: 'active' | 'inactive';
        balance?: number | null;
        balanceAsOf?: number | null;
        onRefresh?: () => void;
        onRelink?: () => void;
        isRefreshing?: boolean;
        canRelink?: boolean;
    }) => (
        <div className="p-4 border-b last:border-b-0">
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="min-w-0 flex-1">
                        <p className="font-medium text-foreground truncate" title={name}>{name}</p>
                        <div className="flex flex-wrap items-center gap-2 mt-1">
                            {status && (
                                <span className="text-sm text-muted-foreground">
                                    Connection: {status === 'active' ? 'Active' : 'Inactive'}
                                </span>
                            )}
                            {renderBalance(balance)}
                            {status === 'inactive' && canRelink && (
                                <Button onClick={onRelink} variant="secondary" size="sm">Reactivate</Button>
                            )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                            {renderBalanceFreshness(balanceAsOf, true)}
                        </div>
                    </div>
                </div>
                {onRefresh && (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onRefresh}
                        disabled={isRefreshing || status === 'inactive'}
                        className="shrink-0"
                        aria-label={`Refresh ${name} account data`}
                    >
                        <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                    </Button>
                )}
            </div>
        </div>
    );

    const renderConnectedAccountCards = (connectedAccount: ConnectedAccount) => {
        if (connectedAccount.venmo) {
            return connectedAccount.venmo.map((venmoUser, index) => {
                const accountKey = `venmo-${venmoUser}`;
                return (
                    <AccountCard
                        key={`${accountKey}-${index}`}
                        name={`Venmo - ${venmoUser}`}
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
                    const canRelink = balances[stripeAccount.id]?.can_relink ?? false;
                    return status === 'active' || (status === 'inactive' && canRelink);
                })
                .map((stripeAccount) => {
                    const { institution_name, display_name, last4, id, status } = stripeAccount;
                    const canRelink = balances[id]?.can_relink ?? false;
                    return (
                        <AccountCard
                            key={`stripe-${id}`}
                            name={`${institution_name} ${display_name} ${last4}`}
                            status={status}
                            balance={balances[id]?.balance}
                            balanceAsOf={balances[id]?.as_of}
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

    const renderInactiveAccountCard = (stripeAccount: StripeAccount) => {
        const canRelink = balances[stripeAccount.id]?.can_relink ?? false;
        return (
            <AccountCard
                key={stripeAccount.id}
                name={`${stripeAccount.institution_name} ${stripeAccount.display_name} ${stripeAccount.last4}`}
                status="inactive"
                balance={balances[stripeAccount.id]?.balance}
                balanceAsOf={balances[stripeAccount.id]?.as_of}
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

            {hasQueryError && (
                <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    <p>
                        {isAccountsError && isBalancesError
                            ? "Connected accounts and balances could not be loaded."
                            : isAccountsError
                                ? "Connected accounts could not be loaded."
                                : "Account balances could not be loaded."}
                        {" "}Missing data is not included in net worth.
                    </p>
                    <Button variant="secondary" size="sm" onClick={retryQueries}>Retry</Button>
                </div>
            )}

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
                    <H4>Active Accounts</H4>

                    {/* Mobile card layout */}
                    <div className="md:hidden">
                        {isLoading ? (
                            <div className="flex justify-center py-8">
                                <Spinner size="md" className="text-muted-foreground" />
                            </div>
                        ) : isAccountsError ? (
                            <Body className="text-center text-muted-foreground py-4">
                                Account list unavailable
                            </Body>
                        ) : activeAccounts.length > 0 ? (
                            <div className="rounded-xl bg-white shadow-sm border overflow-hidden">
                                {activeAccounts.flatMap(renderConnectedAccountCards)}
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
                                {isLoading ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-8">
                                            <Spinner size="md" className="text-muted-foreground mx-auto" />
                                        </TableCell>
                                    </TableRow>
                                ) : isAccountsError ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center text-muted-foreground">
                                            Account list unavailable
                                        </TableCell>
                                    </TableRow>
                                ) : activeAccounts.length > 0 ? (
                                    activeAccounts.flatMap(renderConnectedAccount)
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
                        <H4>
                            Net Worth:{" "}
                            {netWorth != null ? (
                                <StatusBadge status={netWorth >= 0 ? 'success' : 'error'}>
                                    {CurrencyFormatter.format(netWorth)}
                                </StatusBadge>
                            ) : (
                                <span className="text-muted-foreground">Not available</span>
                            )}
                        </H4>
                    </div>

                    <div className="space-y-4">
                        <H4>Inactive Accounts</H4>

                        {/* Mobile card layout */}
                        <div className="md:hidden">
                            {isLoading ? (
                                <div className="flex justify-center py-8">
                                    <Spinner size="md" className="text-muted-foreground" />
                                </div>
                            ) : isAccountsError ? (
                                <Body className="text-center text-muted-foreground py-4">
                                    Account list unavailable
                                </Body>
                            ) : inactiveAccounts.length > 0 ? (
                                <div className="rounded-xl bg-white shadow-sm border overflow-hidden">
                                    {inactiveAccounts.map(renderInactiveAccountCard)}
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
                                    {isLoading ? (
                                        <TableRow>
                                            <TableCell colSpan={3} className="text-center py-8">
                                                <Spinner size="md" className="text-muted-foreground mx-auto" />
                                            </TableCell>
                                        </TableRow>
                                    ) : isAccountsError ? (
                                        <TableRow>
                                            <TableCell colSpan={3} className="text-center text-muted-foreground">
                                                Account list unavailable
                                            </TableCell>
                                        </TableRow>
                                    ) : inactiveAccounts.length > 0 ? (
                                        inactiveAccounts.flatMap(renderStripeAccount)
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
