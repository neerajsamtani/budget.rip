"use client"
import { useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { LineItemInterface } from "@/lib/types";
import {
    TableCell,
    TableRow,
} from "@/components/ui/table"

export default function LineItem({ lineItem, showCheckBox }: {
    lineItem: LineItemInterface;
    showCheckBox?: boolean;
}) {
    // Date formatter
    const longEnUSFormatter = new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
    // Currency formatter
    const currencyFormatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    });

    // Convert the UNIX timestamp to a readable date
    const readableDate = longEnUSFormatter.format(lineItem.date * 1000);
    // Convert the amount to USD
    const readableAmount = currencyFormatter.format(lineItem.amount);

    // Get line items and dispatch from context
    const lineItems = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();

    // Check if the current line item is selected
    const isChecked = lineItems.some(li => li.isSelected && li.id === lineItem._id);

    // Handle checkbox toggle
    const handleToggle = () => {
        lineItemsDispatch({
            type: "toggle_line_item_select",
            lineItemId: lineItem.id
        });
    }

    return (
        <TableRow key={lineItem._id}>
            {!!showCheckBox && <TableCell><input type="checkbox" checked={isChecked} onChange={handleToggle} /></TableCell>}
            <TableCell>{readableDate}</TableCell>
            <TableCell>{lineItem.payment_method}</TableCell>
            <TableCell>{lineItem.description}</TableCell>
            <TableCell>{lineItem.responsible_party}</TableCell>
            <TableCell>{readableAmount}</TableCell>
        </TableRow>
    );
}
