import React from "react";
import { LineItemInterface, useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { Checkbox } from "./ui/checkbox";
import { StatusBadge } from "./ui/status-badge";
import { TableCell, TableRow } from "./ui/table";

interface LineItemProps {
    lineItem: LineItemInterface;
    showCheckBox?: boolean;
}

interface LineItemDisplayProps extends LineItemProps {
    isChecked: boolean;
    handleToggle: () => void;
    amountStatus: 'success' | 'warning';
}

function LineItemCard({ lineItem, showCheckBox, isChecked, handleToggle, amountStatus }: LineItemDisplayProps) {
    const readableDate = DateFormatter.format(lineItem.date * 1000);

    return (
        <div
            className={`p-4 border-b last:border-b-0 ${isChecked ? 'bg-primary-light' : ''}`}
            onClick={showCheckBox ? handleToggle : undefined}
        >
            <div className="flex items-start gap-3">
                {showCheckBox && (
                    <div className="pt-1" onClick={(e) => e.stopPropagation()}>
                        <Checkbox checked={isChecked} onCheckedChange={handleToggle} />
                    </div>
                )}
                <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start gap-2 mb-2">
                        <span className="text-sm text-muted-foreground">{readableDate}</span>
                        <StatusBadge status={amountStatus}>
                            {CurrencyFormatter.format(Math.abs(lineItem.amount))}
                        </StatusBadge>
                    </div>
                    <p className="font-medium text-foreground truncate" title={lineItem.description}>
                        {lineItem.description}
                    </p>
                    <div className="flex gap-2 mt-1 text-sm text-muted-foreground">
                        <span>{lineItem.payment_method}</span>
                        {lineItem.responsible_party && (
                            <>
                                <span>•</span>
                                <span className="truncate">{lineItem.responsible_party}</span>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function LineItemRow({ lineItem, showCheckBox, isChecked, handleToggle, amountStatus }: LineItemDisplayProps) {
    const readableDate = DateFormatter.format(lineItem.date * 1000);

    return (
        <TableRow data-state={isChecked ? 'selected' : undefined}>
            {showCheckBox && (
                <TableCell className="w-12">
                    <Checkbox
                        checked={isChecked}
                        onCheckedChange={handleToggle}
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

export default function LineItem({ lineItem, showCheckBox }: LineItemProps) {
    const lineItems = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const isChecked = lineItems.some(li => li.isSelected && li.id === lineItem.id);

    const handleToggle = () => {
        lineItemsDispatch({
            type: "toggle_line_item_select",
            lineItemId: lineItem.id
        });
    }

    // Determine amount status for color coding
    const amountStatus = lineItem.amount < 0 ? 'success' : 'warning';

    const props = { lineItem, showCheckBox, isChecked, handleToggle, amountStatus };

    // Return only the table row - mobile layout is handled at the page level
    return <LineItemRow {...props} />;
}

// Export the card component for use in mobile card lists
export { LineItemCard };
