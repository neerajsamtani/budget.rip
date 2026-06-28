import { UserPenIcon } from "lucide-react";
import React from "react";
import { useNavigate } from "react-router-dom";
import { LineItemInterface } from "../contexts/LineItemsContext";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { Checkbox } from "./ui/checkbox";
import { StatusBadge } from "./ui/status-badge";
import { TableCell, TableRow } from "./ui/table";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";

interface LineItemProps {
    lineItem: LineItemInterface;
    showCheckBox?: boolean;
    isChecked?: boolean;
    onToggle?: (lineItemId: string) => void;
    detailPath?: string;
}

interface LineItemDisplayProps extends LineItemProps {
    isChecked: boolean;
    handleToggle: () => void;
    amountStatus: 'success' | 'warning';
}

function LineItemCard({ lineItem, showCheckBox, isChecked, handleToggle, amountStatus, detailPath }: LineItemDisplayProps) {
    const readableDate = DateFormatter.format(lineItem.date * 1000);
    const navigate = useNavigate();
    const handleCardClick = detailPath ? () => navigate(detailPath) : showCheckBox ? handleToggle : undefined;

    return (
        <div
            className={`p-4 border-b last:border-b-0 ${isChecked ? 'bg-primary-light' : ''} ${detailPath ? 'cursor-pointer hover:bg-gray-50 transition-colors' : ''}`}
            onClick={handleCardClick}
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

function LineItemRow({ lineItem, showCheckBox, isChecked, handleToggle, amountStatus, detailPath }: LineItemDisplayProps) {
    const readableDate = DateFormatter.format(lineItem.date * 1000);
    const navigate = useNavigate();
    const handleRowNavigation = () => {
        if (detailPath) navigate(detailPath);
    };

    return (
        <TableRow
            data-state={isChecked ? 'selected' : undefined}
            className={detailPath ? "cursor-pointer" : undefined}
            onClick={detailPath ? handleRowNavigation : undefined}
            tabIndex={detailPath ? 0 : undefined}
            onKeyDown={detailPath ? (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    handleRowNavigation();
                }
            } : undefined}
        >
            {showCheckBox && (
                <TableCell className="w-12" onClick={(event) => event.stopPropagation()}>
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
        </TableRow>
    );
}

const LineItem = React.memo(function LineItem({ lineItem, showCheckBox, isChecked = false, onToggle, detailPath }: LineItemProps) {
    const amountStatus: 'success' | 'warning' = lineItem.amount < 0 ? 'success' : 'warning';
    const handleToggle = onToggle ? () => onToggle(lineItem.id) : () => {};
    const props = { lineItem, showCheckBox, isChecked, handleToggle, amountStatus, detailPath };
    return <LineItemRow {...props} />;
});

export default LineItem;

// Export the card component for use in mobile card lists
export { LineItemCard };
