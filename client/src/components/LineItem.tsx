import React from "react";
import { LineItemInterface, useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { DateFormatter } from "../utils/formatters";

interface LineItemProps {
    lineItem: LineItemInterface;
    showCheckBox?: boolean;
}

export default function LineItem({ lineItem, showCheckBox }: LineItemProps) {
    // Convert the UNIX timestamp to a readable date
    const readableDate = DateFormatter.format(lineItem.date * 1000);

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
            {!!showCheckBox && <td><input type="checkbox" checked={isChecked} onChange={handleToggle} /></td>}
            <td>{readableDate}</td>
            <td>{lineItem.payment_method}</td>
            <td>{lineItem.description}</td>
            <td>{lineItem.responsible_party}</td>
            <td>{lineItem.amount}</td>
        </tr>
    );
}
