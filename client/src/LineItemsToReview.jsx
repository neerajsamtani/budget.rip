import React, { useEffect, useState } from "react";
import axios from "axios";
import { Table, Navbar, Button, Nav } from "react-bootstrap";
import LineItem from "./LineItem";
import CreateEventModal from "./CreateEventModal";
import CreateCashTransactionModal from "./CreateCashTransactionModal";

export default function LineItemsToReview() {

    const [lineItems, setLineItems] = useState([])
    const [selectedLineItems, setSelectedLineItems] = useState([])
    const [eventModalShow, setEventModalShow] = useState(false);
    const [cashModalShow, setCashModalShow] = useState(false);

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axios.get(`${REACT_APP_API_ENDPOINT}api/line_items`, {
            params: {
                "only_line_items_to_review": true,
            }
        })
            .then(response => {
                setLineItems(response.data.data)
            })
            .catch(error => console.log(error));
    }, [])

    const padding = {
        padding: 5
    }

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
                        {lineItems.map(lineItem =>
                            <LineItem key={lineItem._id} lineItem={lineItem} selectedLineItems={selectedLineItems} setSelectedLineItems={setSelectedLineItems} />
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
                selectedLineItems={selectedLineItems}
                setSelectedLineItems={setSelectedLineItems}
                onHide={() => setEventModalShow(false)}
            />
            <div className="fixed-bottom">
                <Navbar color="dark" className="justify-content-end">
                    <Nav.Item style={padding}>
                        <Button onClick={() => setCashModalShow(true)} variant="primary">Create Cash Transaction</Button>
                    </Nav.Item>
                    <Nav.Item style={padding}>
                        <Button onClick={() => setEventModalShow(true)} variant="primary">Create Event</Button>
                    </Nav.Item>
                </Navbar>
            </div>
        </div>
    )
}