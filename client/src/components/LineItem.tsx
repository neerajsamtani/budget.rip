import React from "react";
import { LineItemInterface, useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { StatusBadge } from "./ui/status-badge";
import { TableCell, TableRow } from "./ui/table";

interface LineItemProps {
    lineItem: LineItemInterface;
    showCheckBox?: boolean;
}

export default function LineItem({ lineItem, showCheckBox }: LineItemProps) {
    const readableDate = DateFormatter.format(lineItem.date * 1000);
    const lineItems = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const isChecked = lineItems.some(li => li.isSelected && li.id === lineItem._id);

    const handleToggle = () => {
        lineItemsDispatch({
            type: "toggle_line_item_select",
            lineItemId: lineItem.id
        });
    }

    // Determine amount status for color coding
    const amountStatus = lineItem.amount < 0 ? 'success' : 'warning';

    return (
        <TableRow data-state={isChecked ? 'selected' : undefined}>
            {showCheckBox && (
                <TableCell className="w-12">
                    <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={handleToggle}
                        className="w-4 h-4 text-primary bg-white border rounded focus:ring-primary focus:ring-2 focus:ring-offset-2"
                    />
                </TableCell>
            )}
            <TableCell className="font-medium">
                {readableDate}
            </TableCell>
            <TableCell>
                {lineItem.payment_method}
            </TableCell>
            <TableCell className="w-2/5 min-w-0">
                <span className="block" title={lineItem.description}>
                    {lineItem.description}
                </span>
            </TableCell>
            <TableCell className="w-1/5 min-w-0">
                <span className="block" title={lineItem.responsible_party}>
                    {lineItem.responsible_party}
                </span>
            </TableCell>
            <TableCell className="text-right">
                <StatusBadge status={amountStatus}>
                    {CurrencyFormatter.format(Math.abs(lineItem.amount))}
                </StatusBadge>
            </TableCell>
        </TableRow>
    );
}
