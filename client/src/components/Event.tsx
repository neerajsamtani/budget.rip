import React, { useState } from "react";
import { Badge, Button } from "react-bootstrap";
import { LineItemInterface } from "../contexts/LineItemsContext";
import axiosInstance from "../utils/axiosInstance";
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
    const longEnUSFormatter = new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        timeZone: 'UTC'
    });
    const readableDate = longEnUSFormatter.format(event.date * 1000);

    const [eventDetailsModalShow, setEventDetailsModalShow] = useState(false);
    const [lineItemsForEvent, setLineItemsForEvent] = useState<LineItemInterface[]>([])

    const showEventDetails = () => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/events/${event._id}/line_items_for_event`)
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
            <td>{readableDate}</td>
            <td>{event.name}</td>
            <td>{event.category}</td>
            <td>${event.amount.toFixed(2)}</td>
            <td>
                {event.tags && event.tags.length > 0 ? (
                    <div className="d-flex flex-wrap gap-1">
                        {event.tags.map((tag, index) => (
                            <Badge
                                key={index}
                                bg="primary"
                                className="p-2"
                            >
                                {tag}
                            </Badge>
                        ))}
                    </div>
                ) : null}
            </td>
            <td>
                <Button onClick={showEventDetails} variant="secondary">Details</Button>
                <EventDetailsModal
                    show={eventDetailsModalShow}
                    event={event}
                    lineItemsForEvent={lineItemsForEvent}
                    onHide={() => setEventDetailsModalShow(false)}
                />
            </td>
        </>
    )
}
