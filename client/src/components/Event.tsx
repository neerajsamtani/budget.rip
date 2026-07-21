import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableCell, TableRow } from "@/components/ui/table";
import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { StatusBadge } from "../components/ui/status-badge";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";

export interface EventInterface {
    id: string;
    name: string;
    category: string;
    amount: number;
    date: number;
    line_items: string[];
    tags?: string[];
    is_duplicate_transaction?: boolean;
}

export function EventCard({ event }: { event: EventInterface }) {
    const readableDate = DateFormatter.format(event.date * 1000);
    const location = useLocation();
    const amountStatus = event.amount > 0 ? 'warning' : 'success';
    const detailPath = `/events/${event.id}${location.search}`;

    return (
        <Link to={detailPath} className="block no-underline text-inherit">
            <div className="p-4 border-b last:border-b-0 hover:bg-gray-50 transition-colors">
                <div className="flex justify-between items-start gap-2 mb-2">
                    <span className="text-sm text-muted-foreground">{readableDate}</span>
                    <StatusBadge status={amountStatus}>
                        {CurrencyFormatter.format(Math.abs(event.amount))}
                    </StatusBadge>
                </div>
                <p className="font-medium text-foreground mb-2">{event.name}</p>
                <div className="flex flex-wrap items-center gap-2">
                    <Badge className="bg-muted text-foreground border hover:bg-muted">
                        {event.category}
                    </Badge>
                    {event.tags && event.tags.slice(0, 2).map((tag, index) => (
                        <Badge key={index} className="bg-primary text-white px-2 py-1">
                            {tag}
                        </Badge>
                    ))}
                    {event.tags && event.tags.length > 2 && (
                        <span className="text-xs text-muted-foreground">+{event.tags.length - 2} more</span>
                    )}
                </div>
            </div>
        </Link>
    );
}

export default function Event({ event }: { event: EventInterface }) {
    const readableDate = DateFormatter.format(event.date * 1000);
    const location = useLocation();
    const navigate = useNavigate();
    const amountStatus = event.amount > 0 ? 'warning' : 'success';
    const detailPath = `/events/${event.id}${location.search}`;

    return (
        <TableRow
            className="cursor-pointer"
            onClick={() => navigate(detailPath)}
            tabIndex={0}
            onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    navigate(detailPath);
                }
            }}
        >
            <TableCell className="text-sm text-foreground">{readableDate}</TableCell>
            <TableCell className="font-medium text-foreground">{event.name}</TableCell>
            <TableCell>
                <Badge className="bg-muted text-foreground border hover:bg-muted">
                    {event.category}
                </Badge>
            </TableCell>
            <TableCell>
                <StatusBadge status={amountStatus}>
                    {CurrencyFormatter.format(Math.abs(event.amount))}
                </StatusBadge>
            </TableCell>
            <TableCell>
                {event.tags && event.tags.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                        {event.tags.map((tag, index) => (
                            <Badge key={index} className="bg-primary text-white px-2 py-1">
                                {tag}
                            </Badge>
                        ))}
                    </div>
                ) : (
                    <span className="text-muted-foreground text-sm">No tags</span>
                )}
            </TableCell>
            <TableCell>
                <Button asChild variant="secondary" size="sm" onClick={(clickEvent) => clickEvent.stopPropagation()}>
                    <Link to={detailPath}>
                    View Details
                    </Link>
                </Button>
            </TableCell>
        </TableRow>
    )
}
