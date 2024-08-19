import React from "react";
import { useLineItems, useLineItemsDispatch, LineItemInterface } from "./contexts/LineItemsContext";

interface LineItemProps {
    lineItem: LineItemInterface;
    showCheckBox: boolean;
}

export default function LineItem({ lineItem, showCheckBox }: LineItemProps) {
    // Date formatter
    const longEnUSFormatter = new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });

    // Convert the UNIX timestamp to a readable date
    const readableDate = longEnUSFormatter.format(lineItem.date * 1000);

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
        <tr>
            {showCheckBox && <td><input type="checkbox" checked={isChecked} onChange={handleToggle} /></td>}
            <td>{readableDate}</td>
            <td>{lineItem.payment_method}</td>
            <td>{lineItem.description}</td>
            <td>{lineItem.responsible_party}</td>
            <td>{lineItem.amount}</td>
        </tr>
    );
}
