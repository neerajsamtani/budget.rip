"use client"
import { LineItemInterface } from "@/lib/types";
import LineItem from "./LineItem";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { filterInUrlParam } from "./Filter";
import { getLineItems } from "@/lib/data";

export default function LineItemsTable() {

    const searchParams = useSearchParams();
    const payment_method = searchParams.get(filterInUrlParam("Payment Method")) || undefined;
    const month = searchParams.get(filterInUrlParam("Month")) || undefined;
    const year = searchParams.get(filterInUrlParam("Year")) || undefined;

    const [lineItems, setLineItems] = useState<LineItemInterface[]>([]);

    useEffect(() => {
        const fetchLineItems = async () => {
            try {
                const items = await getLineItems({
                    payment_method,
                    year,
                    month,
                });
                setLineItems(items || []);
            } catch (err) {
                console.error("Error fetching line items:", err);
            }
        };

        fetchLineItems();
    }, [payment_method, month, year]);

    return (
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
                    lineItems.map((lineItem: LineItemInterface) => <LineItem key={lineItem._id} lineItem={lineItem} />)
                    :
                    // @ts-expect-error TODO: Need to look into this type error
                    <TableRow align="center"><TableCell colSpan="5">
                        No Line Items found
                    </TableCell></TableRow>
                }
            </TableBody>
        </Table>
    )
}