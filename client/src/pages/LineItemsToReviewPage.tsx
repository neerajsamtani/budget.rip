import React, { useCallback, useEffect, useState } from "react";
import { Button, Nav, Navbar, Table } from "react-bootstrap";
import CreateCashTransactionModal from "../components/CreateCashTransactionModal";
import CreateEventModal from "../components/CreateEventModal";
import LineItem from "../components/LineItem";
import { useLineItems } from "../contexts/LineItemsContext";

export default function LineItemsToReviewPage() {

    const [eventModalShow, setEventModalShow] = useState(false);
    const [cashModalShow, setCashModalShow] = useState(false);
    const lineItems = useLineItems();

    const padding = {
        padding: 5
    }

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
                <Table striped bordered hover>
                    <thead>
                        <tr>
                            <th>Select</th>
                            <th>Date</th>
                            <th>Payment Method</th>
                            <th>Description</th>
                            <th>Name</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {lineItems.length > 0 && lineItems.map(lineItem =>
                            <LineItem key={lineItem._id}
                                lineItem={lineItem}
                                showCheckBox={true}
                            />
                        )}
                    </tbody>
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
            <div className="fixed-bottom">
                <Navbar color="dark" className="justify-content-end">
                    <Nav.Item style={padding}>
                        <Button onClick={() => setCashModalShow(true)} variant="primary">Create Cash Transaction</Button>
                    </Nav.Item>
                    <Nav.Item style={padding}>
                        <Button onClick={() => setEventModalShow(true)} variant="primary">Create Event (↵)</Button>
                    </Nav.Item>
                </Navbar>
            </div>
        </div>
    )
}