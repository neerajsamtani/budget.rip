import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CurrencyFormatter } from "@/utils/formatters";
import React, { useCallback, useEffect, useState } from "react";
import { CornerDownRight } from "lucide-react";
import CreateEventModal from "../components/CreateEventModal";
import CreateManualTransactionModal from "../components/CreateManualTransactionModal";
import CreateSplitwiseExpenseModal from "../components/CreateSplitwiseExpenseModal";
import LineItem, { LineItemCard } from "../components/LineItem";
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
        <div className="flex items-start gap-3 border-l-2 border-primary/30 pl-3 md:pl-4">
            <CornerDownRight className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
            <div className="min-w-0 flex-1">
                <div>
                    <p className="text-sm font-medium text-foreground">Create an event for this line item</p>
                </div>
                <div className={`mt-2 flex ${mobile ? "flex-col" : "items-center"} gap-2`}>
                    <div className={`flex min-w-0 flex-1 ${mobile ? "flex-col items-start" : "items-center"} gap-2`}>
                        <Input
                            aria-label={`Suggested event title for ${lineItem.description}`}
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            onKeyDown={(event) => {
                                if (event.key === "Enter" && name.trim() && !isPending) void accept();
                            }}
                            className="h-9 bg-white"
                        />
                        <Badge className="shrink-0 bg-white text-foreground border hover:bg-white">
                            Category: {suggestion.category}
                        </Badge>
                    </div>
                    <div className="flex shrink-0 gap-2">
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
            </div>
        </div>
    );

    return mobile ? content : (
        <TableRow data-testid={`event-suggestion-${lineItem.id}`} className="bg-muted/30 hover:bg-muted/30">
            <TableCell colSpan={7} className="px-3 pt-0 pb-4 md:px-6 md:pt-0">{content}</TableCell>
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
    const { lineItems, isPending } = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const selectedLineItems = lineItems?.filter(lineItem => lineItem.isSelected) ?? [];
    const total = selectedLineItems.reduce((prev, cur) => prev + cur.amount, 0);

    const handleToggle = useCallback((lineItemId: string) => {
        lineItemsDispatch({ type: "toggle_line_item_select", lineItemId });
    }, [lineItemsDispatch]);

    const handleKeyDown = useCallback((event) => {
        const target = event.target;
        const targetElement = target instanceof HTMLElement ? target : null;
        const isCheckbox = !!targetElement?.closest("[role='checkbox']");
        const isInteractiveTarget = !isCheckbox
            && !!targetElement?.closest("button, input, a, [role='menuitem'], [contenteditable='true']");

        if (event.key === 'Enter' && !event.defaultPrevented && !isInteractiveTarget && selectedLineItems.length > 0 && !eventModalShow && !manualTransactionModalShow) {
            // Radix renders the checkbox as a button. Prevent its native Enter
            // activation from toggling the selection while opening the modal.
            if (isCheckbox) event.preventDefault();
            setEventModalShow(true);
        }
    }, [selectedLineItems.length, eventModalShow, manualTransactionModalShow]);

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

            <div className="space-y-6 pb-32">
                {/* Mobile card layout */}
                <div className="md:hidden rounded-xl bg-white shadow-sm border overflow-hidden">
                    {isPending ? (
                        <div className="flex justify-center py-8">
                            <Spinner size="md" className="text-muted-foreground" />
                        </div>
                    ) : lineItems && lineItems.length > 0 ? (
                        lineItems.map(lineItem => (
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
                                    <div className="border-t border-primary/15 p-3">
                                        <EventSuggestionReview key={lineItem.event_suggestion.id} lineItem={lineItem} mobile />
                                    </div>
                                )}
                            </div>
                        ))
                    ) : (
                        <div className="p-4 text-center text-muted-foreground">
                            No line items to review
                        </div>
                    )}
                </div>

                {/* Desktop table layout */}
                <div className="hidden md:block">
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
                            ) : lineItems && lineItems.length > 0 ? (
                                lineItems.map(lineItem => (
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
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                                        No line items to review
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

            <div className="fixed bottom-0 left-0 right-0 bg-white border-t px-3 py-2 sm:p-4 md:p-6 shadow-lg safe-area-bottom">
                <div className="container mx-auto max-w-7xl">
                    <div className="flex flex-row justify-between items-center gap-2 sm:gap-4">
                        <Body className="text-muted-foreground text-sm sm:text-base whitespace-nowrap">
                            Total: {CurrencyFormatter.format(total)}
                        </Body>
                        <div className="flex flex-row flex-wrap justify-end gap-2 sm:gap-4">
                            <Button onClick={() => { setEventModalShow(false); setSplitwiseExpenseModalShow(false); setManualTransactionModalShow(true); }} variant="secondary" size="sm" className="px-2 sm:px-4">
                                Create Manual Transaction
                            </Button>
                            <Button
                                onClick={() => { setEventModalShow(false); setManualTransactionModalShow(false); setSplitwiseExpenseModalShow(true); }}
                                variant="secondary"
                                size="sm"
                                className="px-2 sm:px-4"
                                disabled={selectedLineItems.length === 0}
                            >
                                Create Splitwise Expense
                            </Button>
                            <Button onClick={() => { setManualTransactionModalShow(false); setSplitwiseExpenseModalShow(false); setEventModalShow(true); }} size="sm" className="px-2 sm:px-4" disabled={selectedLineItems.length === 0}>
                                Create Event<span className="hidden sm:inline"> (↵)</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}
