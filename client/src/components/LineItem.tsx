import { InfoIcon, UserPenIcon } from "lucide-react";
import React, { useState } from "react";
import { LineItemInterface, useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { Button } from "./ui/button";
import { Checkbox } from "./ui/checkbox";
import { StatusBadge } from "./ui/status-badge";
import { TableCell, TableRow } from "./ui/table";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";
import LineItemDetailsModal from "./LineItemDetailsModal";

interface LineItemProps {
    lineItem: LineItemInterface;
    showCheckBox?: boolean;
}

interface LineItemDisplayProps extends LineItemProps {
    isChecked: boolean;
    handleToggle: () => void;
    amountStatus: 'success' | 'warning';
    onShowDetails?: () => void;
}

function LineItemCard({ lineItem, showCheckBox, isChecked, handleToggle, amountStatus, onShowDetails }: LineItemDisplayProps) {
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
                        <div className="flex items-center gap-2">
                            <StatusBadge status={amountStatus}>
                                {CurrencyFormatter.format(Math.abs(lineItem.amount))}
                            </StatusBadge>
                            {onShowDetails && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onShowDetails();
                                    }}
                                    className="h-6 w-6 p-0"
                                >
                                    <InfoIcon className="h-4 w-4" />
                                    <span className="sr-only">View details</span>
                                </Button>
                            )}
                        </div>
                    </div>
                    <p className="font-medium text-foreground truncate" title={lineItem.description}>
                        {lineItem.description}
                    </p>
                    <div className="flex gap-2 mt-1 text-sm text-muted-foreground items-center">
                        <span>{lineItem.payment_method}</span>
                        {lineItem.is_manual && (
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <UserPenIcon className="h-3 w-3 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>Manual transaction</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        )}
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

function LineItemRow({ lineItem, showCheckBox, isChecked, handleToggle, amountStatus, onShowDetails }: LineItemDisplayProps) {
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
                <span className="flex items-center gap-1.5">
                    {lineItem.payment_method}
                    {lineItem.is_manual && (
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <UserPenIcon className="h-3 w-3 text-muted-foreground" />
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>Manual transaction</p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    )}
                </span>
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
            {onShowDetails && (
                <TableCell className="w-12">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onShowDetails}
                        className="h-8 w-8 p-0"
                    >
                        <InfoIcon className="h-4 w-4" />
                        <span className="sr-only">View details</span>
                    </Button>
                </TableCell>
            )}
        </TableRow>
    );
}

export default function LineItem({ lineItem, showCheckBox }: LineItemProps) {
    const { lineItems } = useLineItems();
    const lineItemsDispatch = useLineItemsDispatch();
    const isChecked = (lineItems || []).some(li => li.isSelected && li.id === lineItem.id);
    const [showDetailsModal, setShowDetailsModal] = useState(false);

    const handleToggle = () => {
        lineItemsDispatch({
            type: "toggle_line_item_select",
            lineItemId: lineItem.id
        });
    }

    // Determine amount status for color coding
    const amountStatus: 'success' | 'warning' = lineItem.amount < 0 ? 'success' : 'warning';

    const props = {
        lineItem,
        showCheckBox,
        isChecked,
        handleToggle,
        amountStatus,
        onShowDetails: () => setShowDetailsModal(true)
    };

    return (
        <>
            <LineItemRow {...props} />
            <LineItemDetailsModal
                show={showDetailsModal}
                lineItem={lineItem}
                onHide={() => setShowDetailsModal(false)}
            />
        </>
    );
}

// Export the card component for use in mobile card lists
export { LineItemCard };
