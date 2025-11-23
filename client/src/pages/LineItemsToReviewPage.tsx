import { Button } from "@/components/ui/button";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CurrencyFormatter } from "@/utils/formatters";
import React, { useCallback, useEffect, useState } from "react";
import CreateCashTransactionModal from "../components/CreateCashTransactionModal";
import CreateEventModal from "../components/CreateEventModal";
import LineItem, { LineItemCard } from "../components/LineItem";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import { useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";

// Mobile card wrapper that includes context hooks
function MobileLineItemCard({ lineItem }: { lineItem: any }) {
    const lineItems = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const isChecked = lineItems.some(li => li.isSelected && li.id === lineItem.id);

    const handleToggle = () => {
        lineItemsDispatch({
            type: "toggle_line_item_select",
            lineItemId: lineItem.id
        });
    };

    const amountStatus = lineItem.amount < 0 ? 'success' : 'warning';

    return (
        <LineItemCard
            lineItem={lineItem}
            showCheckBox={true}
            isChecked={isChecked}
            handleToggle={handleToggle}
            amountStatus={amountStatus}
        />
    );
}

export default function LineItemsToReviewPage() {

    const [eventModalShow, setEventModalShow] = useState(false);
    const [cashModalShow, setCashModalShow] = useState(false);
    const lineItems = useLineItems();
    const selectedLineItems = lineItems?.filter(lineItem => lineItem.isSelected) ?? [];
    const total = selectedLineItems.reduce((prev, cur) => prev + cur.amount, 0);


    const handleKeyDown = useCallback((event) => {
        if (event.key === 'Enter') {
            setEventModalShow(true);
        }
    }, []);

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

            {lineItems && (
                <div className="space-y-6 pb-32">
                    {/* Mobile card layout */}
                    <div className="md:hidden rounded-xl bg-white shadow-sm border overflow-hidden">
                        {lineItems.length > 0 && lineItems.map(lineItem => (
                            <MobileLineItemCard key={lineItem.id} lineItem={lineItem} />
                        ))}
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
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {lineItems.length > 0 && lineItems.map(lineItem =>
                                    <LineItem
                                        key={lineItem.id}
                                        lineItem={lineItem}
                                        showCheckBox={true}
                                    />
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </div>
            )}

            <CreateCashTransactionModal
                show={cashModalShow}
                onHide={() => setCashModalShow(false)}
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
                        <div className="flex flex-row gap-2 sm:gap-4">
                            <Button onClick={() => setCashModalShow(true)} variant="secondary" size="sm" className="text-xs sm:text-sm px-2 sm:px-4">
                                Create Cash Transaction
                            </Button>
                            <Button onClick={() => setEventModalShow(true)} size="sm" className="text-xs sm:text-sm px-2 sm:px-4">
                                Create Event<span className="hidden sm:inline"> (↵)</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}