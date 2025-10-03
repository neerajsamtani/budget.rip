import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import LineItem from "../components/LineItem";
import PaymentMethodFilter from "../components/PaymentMethodFilter";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
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
            .catch(error => toast.error("Error", {
                description: error.message,
                duration: 3500,
            }));
    }, [paymentMethod])

    return (
        <PageContainer>
            <PageHeader>
                <H1>Line Items</H1>
                <Body className="text-muted-foreground">
                    Browse all your transaction line items with filtering options
                </Body>
            </PageHeader>

            <div className="space-y-6">
                <div className="flex flex-col sm:flex-row gap-4">
                    <PaymentMethodFilter paymentMethod={paymentMethod} setPaymentMethod={setPaymentMethod} />
                </div>

                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Date</TableHead>
                            <TableHead>Payment Method</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead>Party</TableHead>
                            <TableHead className="text-right">Amount</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {lineItems.length > 0 ? (
                            lineItems.map(lineItem => (
                                <LineItem key={lineItem._id} lineItem={lineItem} />
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={5} className="text-center text-muted-foreground">
                                    No Line Items found
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </PageContainer>
    )
}