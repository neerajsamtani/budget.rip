import { Button } from "@/components/ui/button";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
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
        <div>
            <h1>Line Items To Review</h1>
            {lineItems &&
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Select</TableHead>
                            <TableHead>Date</TableHead>
                            <TableHead>Payment Method</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead>Name</TableHead>
                            <TableHead>Amount</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {lineItems.length > 0 && lineItems.map(lineItem =>
                            <LineItem key={lineItem._id}
                                lineItem={lineItem}
                                showCheckBox={true}
                            />
                        )}
                    </TableBody>
                </Table>
            }
            <CreateCashTransactionModal
                show={cashModalShow}
                onHide={() => setCashModalShow(false)}
            />
            <CreateEventModal
                show={eventModalShow}
                onHide={() => setEventModalShow(false)}
            />
            <div className="fixed bottom-0 left-0 right-0 bg-slate-900 p-4">
                <div className="flex justify-end space-x-4">
                    <Button onClick={() => setCashModalShow(true)}>Create Cash Transaction</Button>
                    <Button onClick={() => setEventModalShow(true)}>Create Event (↵)</Button>
                </div>
            </div>
        </div>
    )
}