import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableCell } from "@/components/ui/table";
import { StatusBadge } from "../components/ui/status-badge";
import { LineItemInterface } from "../contexts/LineItemsContext";
import axiosInstance from "../utils/axiosInstance";
import { DateFormatter, CurrencyFormatter } from "../utils/formatters";
import EventDetailsModal from "./EventDetailsModal";

export interface EventInterface {
    _id: string;
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
    const [lineItemsForEvent, setLineItemsForEvent] = useState<LineItemInterface[]>([])

    const showEventDetails = () => {
        var VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
        axiosInstance.get(`${VITE_API_ENDPOINT}api/events/${event._id}/line_items_for_event`)
            .then(response => {
                setLineItemsForEvent(response.data.data)
            })
            .then(() => {
                setEventDetailsModalShow(true)
            })
            .catch(error => console.log(error));
    }

    return (
        <>
            <TableCell className="font-mono text-sm text-[#374151]">
                {readableDate}
            </TableCell>
            <TableCell className="font-medium text-[#374151]">
                {event.name}
            </TableCell>
            <TableCell>
                <Badge className="bg-[#F5F5F5] text-[#374151] border border-[#E0E0E0] hover:bg-[#E0E0E0]">
                    {event.category}
                </Badge>
            </TableCell>
            <TableCell>
                <StatusBadge
                    status={event.category === 'Income' ? 'success' : event.amount > 0 ? 'warning' : 'success'}
                >
                    {CurrencyFormatter.format(event.amount)}
                </StatusBadge>
            </TableCell>
            <TableCell>
                {event.tags && event.tags.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                        {event.tags.map((tag, index) => (
                            <Badge
                                key={index}
                                className="bg-[#5B82C4] text-white text-xs px-2 py-1"
                            >
                                {tag}
                            </Badge>
                        ))}
                    </div>
                ) : (
                    <span className="text-[#9CA3AF] text-sm">No tags</span>
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
