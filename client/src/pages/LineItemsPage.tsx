import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import LineItem from "../components/LineItem";
import PaymentMethodFilter from "../components/PaymentMethodFilter";
import { LineItemInterface } from "../contexts/LineItemsContext";
import axiosInstance from "../utils/axiosInstance";

export default function LineItemsPage() {

    const [lineItems, setLineItems] = useState<LineItemInterface[]>([]);
    const [paymentMethod, setPaymentMethod] = useState("All")

    useEffect(() => {
        var VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
        axiosInstance.get(`${VITE_API_ENDPOINT}api/line_items`, {
            params: {
                "payment_method": paymentMethod,
            }
        })
            .then(response => {
                setLineItems(response.data.data)
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