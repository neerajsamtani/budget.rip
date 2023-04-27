import React from "react";
import { useLineItems, useLineItemsDispatch } from "./contexts/LineItemsContext";

export default function LineItem({ lineItem, showCheckBox }) {
    const longEnUSFormatter = new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
    const readableDate = longEnUSFormatter.format(lineItem.date * 1000);

    const lineItems = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const isChecked = lineItems.filter(li => li.isSelected).filter(li => li.id === lineItem._id).length > 0;

    const handleToggle = () => {
        lineItemsDispatch({
            type: "toggle_line_item_select",
            lineItemId: lineItem.id
        })
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
    )
}