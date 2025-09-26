import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import React, { useEffect, useState } from "react";
import LineItem from "../components/LineItem";
import PaymentMethodFilter from "../components/PaymentMethodFilter";
import { LineItemInterface } from "../contexts/LineItemsContext";
import axiosInstance from "../utils/axiosInstance";

export default function LineItemsPage() {

    const [lineItems, setLineItems] = useState<LineItemInterface[]>([]);
    const [paymentMethod, setPaymentMethod] = useState("All")

    useEffect(() => {
        const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
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
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Payment Method</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Amount</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {lineItems.length > 0 ?
                        lineItems.map(lineItem => <LineItem key={lineItem._id} lineItem={lineItem} />)
                        :
                        <TableRow>
                            <TableCell colSpan={5} className="text-center">
                                No Line Items found
                            </TableCell>
                        </TableRow>
                    }
                </TableBody>
            </Table>
        </div>
    )
}