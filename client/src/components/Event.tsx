import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableCell } from "@/components/ui/table";
import React, { useState, useEffect } from "react";
import { StatusBadge } from "../components/ui/status-badge";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import EventDetailsModal from "./EventDetailsModal";
import { useEventLineItems } from "../hooks/useApi";
import { showErrorToast } from "../utils/toast-helpers";

export interface EventInterface {
    _id: string;
    id: string;
    name: string;
    category: string;
    amount: number;
    date: number; // Assuming date is a Unix timestamp in seconds
    line_items: string[];
    tags?: string[];
}

export default function Event({ event }: { event: EventInterface }) {
    const readableDate = DateFormatter.format(event.date * 1000);

    const [eventDetailsModalShow, setEventDetailsModalShow] = useState(false);
    const [shouldFetch, setShouldFetch] = useState(false);

    const { data: lineItemsForEvent = [], error } = useEventLineItems(shouldFetch ? event.id : '');

    useEffect(() => {
        if (error) {
            showErrorToast(error);
        }
    }, [error]);

    const showEventDetails = () => {
        setShouldFetch(true);
        setEventDetailsModalShow(true);
    }

    return (
        <>
            <TableCell className="text-sm text-foreground">
                {readableDate}
            </TableCell>
            <TableCell className="font-medium text-foreground">
                {event.name}
            </TableCell>
            <TableCell>
                <Badge className="bg-muted text-foreground border hover:bg-muted">
                    {event.category}
                </Badge>
            </TableCell>
            <TableCell>
                <StatusBadge
                    status={event.amount > 0 ? 'warning' : 'success'}
                >
                    {CurrencyFormatter.format(Math.abs(event.amount))}
                </StatusBadge>
            </TableCell>
            <TableCell>
                {event.tags && event.tags.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                        {event.tags.map((tag, index) => (
                            <Badge
                                key={index}
                                className="bg-primary text-white text-xs px-2 py-1"
                            >
                                {tag}
                            </Badge>
                        ))}
                    </div>
                ) : (
                    <span className="text-muted-foreground text-sm">No tags</span>
                )}
            </TableCell>
            <TableCell>
                <Button
                    onClick={showEventDetails}
                    variant="secondary"
                    size="sm"
                    className="text-xs"
                >
                    View Details
                </Button>
                <EventDetailsModal
                    show={eventDetailsModalShow}
                    event={event}
                    lineItemsForEvent={lineItemsForEvent}
                    onHide={() => setEventDetailsModalShow(false)}
                />
            </TableCell>
        </>
    )
}
