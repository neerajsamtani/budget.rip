import { Button } from "@/components/ui/button";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { H1, Body } from "../components/ui/typography";
import React, { useCallback, useEffect, useState } from "react";
import CreateCashTransactionModal from "../components/CreateCashTransactionModal";
import CreateEventModal from "../components/CreateEventModal";
import LineItem from "../components/LineItem";
import { useLineItems } from "../contexts/LineItemsContext";

export default function LineItemsToReviewPage() {

    const [eventModalShow, setEventModalShow] = useState(false);
    const [cashModalShow, setCashModalShow] = useState(false);
    const lineItems = useLineItems();


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
                <Body className="text-[#6B7280]">
                    Review and categorize your recent transactions
                </Body>
            </PageHeader>

            {lineItems && (
                <div className="space-y-6">
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
                                    key={lineItem._id}
                                    lineItem={lineItem}
                                    showCheckBox={true}
                                />
                            )}
                        </TableBody>
                    </Table>
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

            <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#E0E0E0] p-6 shadow-lg">
                <div className="container mx-auto max-w-7xl">
                    <div className="flex justify-end space-x-4">
                        <Button onClick={() => setCashModalShow(true)} variant="secondary">
                            Create Cash Transaction
                        </Button>
                        <Button onClick={() => setEventModalShow(true)}>
                            Create Event (↵)
                        </Button>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}