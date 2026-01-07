import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CurrencyFormatter } from "@/utils/formatters";
import React, { useCallback, useEffect, useState } from "react";
import CreateCashTransactionModal from "../components/CreateCashTransactionModal";
import CreateEventModal from "../components/CreateEventModal";
import LineItem, { LineItemCard } from "../components/LineItem";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import { LineItemInterface, useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { useDeleteCashTransaction } from "../hooks/useApi";
import { showErrorToast, showSuccessToast } from "../utils/toast-helpers";

// Mobile card wrapper that includes context hooks
interface MobileLineItemCardProps {
    lineItem: LineItemInterface;
    onDelete?: (id: string) => void;
    isDeleting?: boolean;
}

function MobileLineItemCard({ lineItem, onDelete, isDeleting }: MobileLineItemCardProps) {
    const { lineItems } = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const isChecked = (lineItems || []).some(li => li.isSelected && li.id === lineItem.id);

    const handleToggle = () => {
        lineItemsDispatch({
            type: "toggle_line_item_select",
            lineItemId: lineItem.id
        });
    };

    const amountStatus: 'success' | 'warning' = lineItem.amount < 0 ? 'success' : 'warning';

    return (
        <LineItemCard
            lineItem={lineItem}
            showCheckBox={true}
            isChecked={isChecked}
            handleToggle={handleToggle}
            amountStatus={amountStatus}
            onDelete={onDelete}
            isDeleting={isDeleting}
        />
    );
}

export default function LineItemsToReviewPage() {

    const [eventModalShow, setEventModalShow] = useState(false);
    const [cashModalShow, setCashModalShow] = useState(false);
    const [deletingLineItemId, setDeletingLineItemId] = useState<string | null>(null);
    const { lineItems, isLoading } = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const selectedLineItems = lineItems?.filter(lineItem => lineItem.isSelected) ?? [];
    const total = selectedLineItems.reduce((prev, cur) => prev + cur.amount, 0);

    const deleteCashTransactionMutation = useDeleteCashTransaction();

    const handleDelete = (lineItemId: string) => {
        deleteCashTransactionMutation.mutate(lineItemId, {
            onSuccess: () => {
                lineItemsDispatch({ type: "remove_line_items", lineItemIds: [lineItemId] });
                showSuccessToast("Cash transaction deleted");
                setDeletingLineItemId(null);
            },
            onError: (error) => {
                showErrorToast(error);
                setDeletingLineItemId(null);
            },
        });
    };

    const handleKeyDown = useCallback((event: KeyboardEvent) => {
        if (event.key === 'Enter' && selectedLineItems.length > 0 && !eventModalShow && !cashModalShow) {
            setEventModalShow(true);
        }
    }, [selectedLineItems.length, eventModalShow, cashModalShow]);

    useEffect(() => {
        document.addEventListener('keydown', handleKeyDown);

        // Cleanup the event listener on component unmount
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
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
                    {isLoading ? (
                        <div className="flex justify-center py-8">
                            <Spinner size="md" className="text-muted-foreground" />
                        </div>
                    ) : lineItems && lineItems.length > 0 ? (
                        lineItems.map(lineItem => (
                            <MobileLineItemCard
                                key={lineItem.id}
                                lineItem={lineItem}
                                onDelete={lineItem.payment_method === "Cash" ? (id) => setDeletingLineItemId(id) : undefined}
                                isDeleting={deleteCashTransactionMutation.isPending && deletingLineItemId === lineItem.id}
                            />
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
                                <TableHead className="w-12"></TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center py-8">
                                        <Spinner size="md" className="text-muted-foreground mx-auto" />
                                    </TableCell>
                                </TableRow>
                            ) : lineItems && lineItems.length > 0 ? (
                                lineItems.map(lineItem =>
                                    <LineItem
                                        key={lineItem.id}
                                        lineItem={lineItem}
                                        showCheckBox={true}
                                        onDelete={lineItem.payment_method === "Cash" ? (id) => setDeletingLineItemId(id) : undefined}
                                        isDeleting={deleteCashTransactionMutation.isPending && deletingLineItemId === lineItem.id}
                                    />
                                )
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

            <CreateCashTransactionModal
                show={cashModalShow}
                onHide={() => setCashModalShow(false)}
            />
            <CreateEventModal
                show={eventModalShow}
                onHide={() => setEventModalShow(false)}
            />

            {/* Delete confirmation dialog */}
            <AlertDialog open={deletingLineItemId !== null} onOpenChange={(open) => !open && setDeletingLineItemId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Cash Transaction</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete this cash transaction? This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={() => deletingLineItemId && handleDelete(deletingLineItemId)}
                            disabled={deleteCashTransactionMutation.isPending}
                            className="bg-semantic-error text-white hover:bg-semantic-error-dark focus-visible:ring-semantic-error"
                        >
                            {deleteCashTransactionMutation.isPending ? <Spinner size="sm" /> : "Delete"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            <div className="fixed bottom-0 left-0 right-0 bg-white border-t px-3 py-2 sm:p-4 md:p-6 shadow-lg safe-area-bottom">
                <div className="container mx-auto max-w-7xl">
                    <div className="flex flex-row justify-between items-center gap-2 sm:gap-4">
                        <Body className="text-muted-foreground text-sm sm:text-base whitespace-nowrap">
                            Total: {CurrencyFormatter.format(total)}
                        </Body>
                        <div className="flex flex-row gap-2 sm:gap-4">
                            <Button onClick={() => { setEventModalShow(false); setCashModalShow(true); }} variant="secondary" size="sm" className="px-2 sm:px-4">
                                Create Cash Transaction
                            </Button>
                            <Button onClick={() => { setCashModalShow(false); setEventModalShow(true); }} size="sm" className="px-2 sm:px-4" disabled={selectedLineItems.length === 0}>
                                Create Event<span className="hidden sm:inline"> (↵)</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}