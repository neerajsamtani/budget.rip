import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import LineItem from "./LineItem";
import PaymentMethodFilter from "./PaymentMethodFilter";
import axios from "axios";

export default function LineItems() {

    const [lineItems, setLineItems] = useState([])
    const [total, setTotal] = useState(0)
    const [paymentMethod, setPaymentMethod] = useState("All")

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axios.get(`${REACT_APP_API_ENDPOINT}api/line_items`, { params: {
            "payment_method": paymentMethod,
        }})
        .then(response => {
            setLineItems(response.data.data)
            setTotal(response.data.total)
        })
        .catch(error => console.log(error));
    }, [paymentMethod])

    return(
        <div>
            <h1>Line Items</h1>
            <p>Total: ${total}</p>
            <PaymentMethodFilter paymentMethod={paymentMethod} setPaymentMethod={setPaymentMethod} />
            {lineItems && 
            <Table striped bordered hover>
                <thead>
                    <tr>
                    <th>Date</th>
                    <th>Payment Method</th>
                    <th>Description</th>
                    <th>Name</th>
                    <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                {lineItems.map(lineItem => 
                    <LineItem key={lineItem._id} lineItem={lineItem} />
                )}
                </tbody>
            </Table>
            }
            {/* {lineItems && JSON.stringify(lineItems, null, 2)} */}
        </div>
    )
}