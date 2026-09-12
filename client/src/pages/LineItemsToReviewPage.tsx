import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CurrencyFormatter } from "@/utils/formatters";
import { DateTime } from "luxon";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp, CornerDownRight, Filter, Plus } from "lucide-react";
import CreateEventModal from "../components/CreateEventModal";
import CreateManualTransactionModal from "../components/CreateManualTransactionModal";
import CreateSplitwiseExpenseModal from "../components/CreateSplitwiseExpenseModal";
import LineItem, { LineItemCard } from "../components/LineItem";
import PaymentMethodFilter from "../components/PaymentMethodFilter";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import { LineItemInterface, useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { useAcceptEventSuggestion, useRejectEventSuggestion } from "../hooks/useApi";
import { showErrorToast, showSuccessToast } from "../utils/toast-helpers";

function EventSuggestionReview({ lineItem, mobile = false }: { lineItem: LineItemInterface; mobile?: boolean }) {
    const suggestion = lineItem.event_suggestion;
    const [name, setName] = useState(suggestion?.name ?? "");
    const acceptSuggestion = useAcceptEventSuggestion();
    const rejectSuggestion = useRejectEventSuggestion();
    const lineItemsDispatch = useLineItemsDispatch();

    if (!suggestion) return null;

    const accept = async () => {
        try {
            const event = await acceptSuggestion.mutateAsync({ suggestionId: suggestion.id, name: name.trim() });
            lineItemsDispatch({ type: "remove_line_items", lineItemIds: [lineItem.id] });
            showSuccessToast(event.name, "Created Event");
        } catch (error) {
            showErrorToast(error);
        }
    };

    const reject = async () => {
        try {
            await rejectSuggestion.mutateAsync(suggestion.id);
            lineItemsDispatch({ type: "dismiss_event_suggestion", lineItemId: lineItem.id });
        } catch (error) {
            showErrorToast(error);
        }
    };

    const isPending = acceptSuggestion.isPending || rejectSuggestion.isPending;
    const content = (
        <div className="flex flex-wrap items-center gap-2 border-l-2 border-primary/30 pl-2 xl:flex-nowrap" aria-label={`Suggested event for ${lineItem.description}`}>
            <span className={`flex shrink-0 items-center gap-1.5 text-xs font-medium text-primary ${mobile ? "basis-full" : ""}`}>
                <CornerDownRight className="h-4 w-4" aria-hidden="true" />
                Suggested event
            </span>
            <Input
                aria-label={`Suggested event title for ${lineItem.description}`}
                value={name}
                onChange={event => setName(event.target.value)}
                onKeyDown={event => {
                    if (event.key === "Enter" && name.trim() && !isPending) void accept();
                }}
                className={`h-9 min-w-0 bg-white ${mobile ? "basis-full" : "flex-1"}`}
            />
            <Badge className="max-w-full whitespace-normal bg-white text-foreground border hover:bg-white">
                {suggestion.category}
            </Badge>
            <div className="ml-auto flex shrink-0 gap-2">
                <Button
                    aria-label={`Create event from ${lineItem.description}`}
                    size="sm"
                    onClick={() => void accept()}
                    disabled={!name.trim() || isPending}
                >
                    {acceptSuggestion.isPending ? <Spinner size="sm" /> : "Create event"}
                </Button>
                <Button
                    aria-label={`Dismiss suggestion for ${lineItem.description}`}
                    size="sm"
                    variant="secondary"
                    onClick={() => void reject()}
                    disabled={isPending}
                >
                    Dismiss
                </Button>
            </div>
        </div>
    );

    return mobile ? content : (
        <TableRow data-testid={`event-suggestion-${lineItem.id}`} className="bg-muted/30 hover:bg-muted/30">
            <TableCell colSpan={7} className="px-3 py-2 md:px-4">{content}</TableCell>
        </TableRow>
    );
}

const MobileLineItemCard = React.memo(function MobileLineItemCard({ lineItem, isChecked, onToggle }: { lineItem: LineItemInterface; isChecked: boolean; onToggle: (lineItemId: string) => void }) {
    const amountStatus: 'success' | 'warning' = lineItem.amount < 0 ? 'success' : 'warning';
    const detailPath = `/line_items/${lineItem.id}?returnTo=${encodeURIComponent("/")}`;

    return (
        <LineItemCard
            lineItem={lineItem}
            showCheckBox={true}
            isChecked={isChecked}
            handleToggle={() => onToggle(lineItem.id)}
            amountStatus={amountStatus}
            detailPath={detailPath}
            hasAttachedContent={!!lineItem.event_suggestion}
        />
    );
});

export default function LineItemsToReviewPage() {
    const [eventModalShow, setEventModalShow] = useState(false);
    const [manualTransactionModalShow, setManualTransactionModalShow] = useState(false);
    const [splitwiseExpenseModalShow, setSplitwiseExpenseModalShow] = useState(false);
    const [addMenuOpen, setAddMenuOpen] = useState(false);
    const [filtersOpen, setFiltersOpen] = useState(false);
    const [search, setSearch] = useState("");
    const [paymentMethod, setPaymentMethod] = useState("All");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const { lineItems, isPending, error, refetch } = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const allLineItems = lineItems ?? [];
    const selectedLineItems = allLineItems.filter(lineItem => lineItem.isSelected);
    const total = selectedLineItems.reduce((prev, cur) => prev + cur.amount, 0);

    const hasFilters = Boolean(search.trim() || paymentMethod !== "All" || startDate || endDate);
    const activeFilterCount = [Boolean(search.trim()), paymentMethod !== "All", Boolean(startDate), Boolean(endDate)].filter(Boolean).length;

    const visibleLineItems = useMemo(() => {
        const normalizedSearch = search.trim().toLowerCase();
        return allLineItems.filter(lineItem => {
            const matchesSearch = !normalizedSearch
                || [lineItem.description, lineItem.responsible_party]
                    .filter(Boolean)
                    .some(value => value.toLowerCase().includes(normalizedSearch));
            const matchesPaymentMethod = paymentMethod === "All" || lineItem.payment_method === paymentMethod;
            const date = DateTime.fromSeconds(lineItem.date, { zone: "utc" }).toISODate() || "";
            const matchesStartDate = !startDate || date >= startDate;
            const matchesEndDate = !endDate || date <= endDate;
            return matchesSearch && matchesPaymentMethod && matchesStartDate && matchesEndDate;
        });
    }, [allLineItems, endDate, paymentMethod, search, startDate]);

    const hiddenSelectionCount = selectedLineItems.filter(
        lineItem => !visibleLineItems.some(visibleLineItem => visibleLineItem.id === lineItem.id)
    ).length;

    const handleToggle = useCallback((lineItemId: string) => {
        lineItemsDispatch({ type: "toggle_line_item_select", lineItemId });
    }, [lineItemsDispatch]);

    const handleKeyDown = useCallback((event) => {
        const target = event.target;
        const targetElement = target instanceof HTMLElement ? target : null;
        const isCheckbox = !!targetElement?.closest("[role='checkbox']");
        const isInteractiveTarget = !isCheckbox
            && !!targetElement?.closest("button, input, textarea, select, a, [role='menuitem'], [role='combobox'], [role='textbox'], [contenteditable='true']");

        if (event.key === 'Enter' && !event.defaultPrevented && !isInteractiveTarget && selectedLineItems.length > 0 && !eventModalShow && !manualTransactionModalShow && !splitwiseExpenseModalShow) {
            // Radix renders the checkbox as a button. Prevent its native Enter
            // activation from toggling the selection while opening the modal.
            if (isCheckbox) event.preventDefault();
            setEventModalShow(true);
        }
    }, [selectedLineItems.length, eventModalShow, manualTransactionModalShow, splitwiseExpenseModalShow]);

    useEffect(() => {
        // Capture the shortcut before Radix Checkbox consumes Enter.
        document.addEventListener('keydown', handleKeyDown, true);

        // Cleanup the event listener on component unmount
        return () => {
            document.removeEventListener('keydown', handleKeyDown, true);
        };
    }, [handleKeyDown]); // Re-run effect if handleKeyDown changes

    return (
        <PageContainer>
            <PageHeader>
                <H1>Review Line Items</H1>
                <Body className="text-muted-foreground">
                    Review and categorize your recent transactions
                </Body>
            </PageHeader>

            <div className="space-y-4 pb-28">
                <div className="space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="text-sm text-muted-foreground" aria-live="polite">
                            <span className="font-semibold text-foreground">{visibleLineItems.length}</span> of {allLineItems.length} to review
                        </p>
                        <div className="xl:hidden">
                            <Button
                                type="button"
                                variant="secondary"
                                size="sm"
                                onClick={() => setFiltersOpen(open => !open)}
                                aria-expanded={filtersOpen}
                                aria-controls="review-filters"
                            >
                                <Filter className="h-4 w-4" />
                                Filters{activeFilterCount > 0 ? ` (${activeFilterCount})` : ""}
                                {filtersOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            </Button>
                        </div>
                    </div>

                    <div id="review-filters" className={`${filtersOpen ? "block" : "hidden"} xl:block rounded-lg border bg-white p-3`}>
                        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto] md:items-end">
                            <div className="space-y-1">
                                <Label htmlFor="review-search" className="text-sm font-medium text-foreground">Search</Label>
                                <Input
                                    id="review-search"
                                    type="search"
                                    value={search}
                                    onChange={event => setSearch(event.target.value)}
                                    placeholder="Description or responsible party"
                                    aria-label="Search review transactions"
                                />
                            </div>
                            <PaymentMethodFilter paymentMethod={paymentMethod} setPaymentMethod={setPaymentMethod} />
                            <div className="space-y-1">
                                <Label htmlFor="review-start-date" className="text-sm font-medium text-foreground">Start date</Label>
                                <Input id="review-start-date" type="date" value={startDate} onChange={event => setStartDate(event.target.value)} />
                            </div>
                            <div className="space-y-1">
                                <Label htmlFor="review-end-date" className="text-sm font-medium text-foreground">End date</Label>
                                <Input id="review-end-date" type="date" value={endDate} onChange={event => setEndDate(event.target.value)} />
                            </div>
                            <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                    setSearch("");
                                    setPaymentMethod("All");
                                    setStartDate("");
                                    setEndDate("");
                                }}
                                disabled={!hasFilters}
                            >
                                Clear filters
                            </Button>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-semantic-error/30 bg-red-50 p-3 text-sm text-semantic-error" role="alert">
                        <span>Review transactions could not be loaded. Your current selection was kept.</span>
                        <Button type="button" variant="outline" size="sm" onClick={() => void refetch?.()}>
                            Retry
                        </Button>
                    </div>
                )}

                {/* Mobile card layout */}
                <div className="xl:hidden rounded-xl bg-white shadow-sm border overflow-hidden">
                    {isPending ? (
                        <div className="flex justify-center py-8">
                            <Spinner size="md" className="text-muted-foreground" />
                        </div>
                    ) : error ? (
                        <div className="p-4 text-center text-semantic-error">Unable to display review transactions.</div>
                    ) : visibleLineItems.length > 0 ? (
                        visibleLineItems.map(lineItem => (
                            <div
                                key={lineItem.id}
                                className={lineItem.event_suggestion ? "m-2 overflow-hidden rounded-lg border border-primary/20 bg-muted/30" : undefined}
                            >
                                <MobileLineItemCard
                                    lineItem={lineItem}
                                    isChecked={!!lineItem.isSelected}
                                    onToggle={handleToggle}
                                />
                                {lineItem.event_suggestion && (
                                    <div className="border-t border-primary/15 px-3 py-2">
                                        <EventSuggestionReview key={lineItem.event_suggestion.id} lineItem={lineItem} mobile />
                                    </div>
                                )}
                            </div>
                        ))
                    ) : allLineItems.length > 0 && hasFilters ? (
                        <div className="space-y-3 p-4 text-center text-muted-foreground">
                            <p>No matching transactions</p>
                            <Button type="button" variant="secondary" size="sm" onClick={() => {
                                setSearch("");
                                setPaymentMethod("All");
                                setStartDate("");
                                setEndDate("");
                            }}>Clear filters</Button>
                        </div>
                    ) : allLineItems.length === 0 ? (
                        <div className="p-4 text-center text-muted-foreground">All caught up</div>
                    ) : (
                        <div className="p-4 text-center text-muted-foreground">
                            No matching transactions
                        </div>
                    )}
                </div>

                {/* Desktop table layout */}
                <div className="hidden xl:block">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Select</TableHead>
                                <TableHead>Date</TableHead>
                                <TableHead>Payment Method</TableHead>
                                <TableHead>Description</TableHead>
                                <TableHead>Party</TableHead>
                                <TableHead className="text-right">Amount</TableHead>
                                <TableHead className="w-12 text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isPending ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center py-8">
                                        <Spinner size="md" className="text-muted-foreground mx-auto" />
                                    </TableCell>
                                </TableRow>
                            ) : error ? (
                                <TableRow><TableCell colSpan={7} className="text-center text-semantic-error">Unable to display review transactions.</TableCell></TableRow>
                            ) : visibleLineItems.length > 0 ? (
                                visibleLineItems.map(lineItem => (
                                    <React.Fragment key={lineItem.id}>
                                        <LineItem
                                            lineItem={lineItem}
                                            showCheckBox={true}
                                            isChecked={!!lineItem.isSelected}
                                            onToggle={handleToggle}
                                            detailPath={`/line_items/${lineItem.id}?returnTo=${encodeURIComponent("/")}`}
                                            hasAttachedContent={!!lineItem.event_suggestion}
                                        />
                                        {lineItem.event_suggestion && (
                                            <EventSuggestionReview key={lineItem.event_suggestion.id} lineItem={lineItem} />
                                        )}
                                    </React.Fragment>
                                ))
                            ) : allLineItems.length > 0 && hasFilters ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                                        <div className="flex flex-col items-center gap-3"><span>No matching transactions</span><Button type="button" variant="secondary" size="sm" onClick={() => { setSearch(""); setPaymentMethod("All"); setStartDate(""); setEndDate(""); }}>Clear filters</Button></div>
                                    </TableCell>
                                </TableRow>
                            ) : allLineItems.length === 0 ? (
                                <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">All caught up</TableCell></TableRow>
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                                        No matching transactions
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </div>
            </div>

            <CreateManualTransactionModal
                show={manualTransactionModalShow}
                onHide={() => setManualTransactionModalShow(false)}
            />
            <CreateSplitwiseExpenseModal
                show={splitwiseExpenseModalShow}
                onHide={() => setSplitwiseExpenseModalShow(false)}
                selectedLineItems={selectedLineItems}
            />
            <CreateEventModal
                show={eventModalShow}
                onHide={() => setEventModalShow(false)}
            />

            <div className="fixed bottom-0 left-0 right-0 z-40 border-t bg-white px-3 py-2 shadow-lg safe-area-bottom">
                <div className="container mx-auto max-w-7xl">
                    <div className="flex flex-wrap items-center justify-between gap-1">
                        <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-foreground">
                                {selectedLineItems.length > 0 ? `${selectedLineItems.length} selected` : "Select transactions to create an event"}
                            </p>
                            {selectedLineItems.length > 0 && (
                                <p className="text-sm tabular-nums text-muted-foreground">
                                    Selected total: {CurrencyFormatter.format(total)}
                                </p>
                            )}
                            {hiddenSelectionCount > 0 && (
                                <p className="text-xs text-muted-foreground">{hiddenSelectionCount} selected hidden by filters</p>
                            )}
                        </div>
                        <div className="flex min-w-0 shrink-0 flex-wrap items-center justify-end gap-1">
                            {selectedLineItems.length > 0 && (
                                <Button type="button" onClick={() => lineItemsDispatch({ type: "clear_line_item_selection" })} variant="ghost" size="sm" className="px-2 text-sm">
                                    Clear selection
                                </Button>
                            )}
                            <Popover open={addMenuOpen} onOpenChange={setAddMenuOpen}>
                                <PopoverTrigger asChild>
                                    <Button type="button" variant="secondary" size="sm" className="px-2 text-sm" aria-label="Add transaction">
                                        <Plus className="h-4 w-4" />
                                        Add
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent align="end" className="w-64 p-2">
                                    <div className="flex flex-col gap-1">
                                        <Button type="button" variant="ghost" size="sm" className="justify-start" onClick={() => { setAddMenuOpen(false); setEventModalShow(false); setSplitwiseExpenseModalShow(false); setManualTransactionModalShow(true); }}>
                                            Create manual transaction
                                        </Button>
                                        <Button type="button" variant="ghost" size="sm" className="justify-start" disabled={selectedLineItems.length === 0} onClick={() => { setAddMenuOpen(false); setEventModalShow(false); setManualTransactionModalShow(false); setSplitwiseExpenseModalShow(true); }}>
                                            Create Splitwise expense
                                        </Button>
                                    </div>
                                </PopoverContent>
                            </Popover>
                            <Button type="button" onClick={() => { setManualTransactionModalShow(false); setSplitwiseExpenseModalShow(false); setEventModalShow(true); }} size="sm" className="px-2 text-sm" disabled={selectedLineItems.length === 0}>
                                Create event<span className="hidden sm:inline"> (↵)</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}
