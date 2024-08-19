import axiosInstance from "../utils/axiosInstance";
import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import LineItem from "../components/LineItem";
import PaymentMethodFilter from "../components/PaymentMethodFilter";

export default function LineItemsPage() {

    const lineItems = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const [paymentMethod, setPaymentMethod] = useState("All")

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/line_items`, {
            params: {
                "payment_method": paymentMethod,
            }
        })
            .then(response => {
                lineItemsDispatch({
                    type: "populate_line_items",
                    fetchedLineItems: response.data.data
                })
            })
            .catch(error => console.log(error));
    }, [paymentMethod])

    return (
        <div>
            <h1>Line Items</h1>
            <PaymentMethodFilter paymentMethod={paymentMethod} setPaymentMethod={setPaymentMethod} />
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
                    {lineItems.length > 0 ?
                        lineItems.map(lineItem => <LineItem key={lineItem._id} lineItem={lineItem} />)
                        :
                        // @ts-expect-error TODO: Need to look into this type error
                        <tr align="center"><td colSpan="5">
                            No Line Items found
                        </td></tr>
                    }
                </tbody>
            </Table>
        </div>
    )
}