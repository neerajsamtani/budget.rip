import React, { useState } from "react";
import { Button } from "react-bootstrap";
import { LineItemInterface } from "../contexts/LineItemsContext";
import EventDetailsModal from "./EventDetailsModal";
import axiosInstance from "../utils/axiosInstance";

export type EventInterface = {
    _id: string;
    date: number; // Assuming `date` is a Unix timestamp in seconds
    name: string;
    category: string;
    amount: number;
};

export default function Event({ event }: { event: EventInterface }) {
    const longEnUSFormatter = new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
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

    // February 14, 2020
    return (
        <tr>
            <td>{readableDate}</td>
            <td>{event.name}</td>
            <td>{event.category}</td>
            <td>{event.amount}</td>
            <td>
                <Button onClick={showEventDetails} variant="secondary">Details</Button>
                <EventDetailsModal
                    show={eventDetailsModalShow}
                    event={event}
                    lineItemsForEvent={lineItemsForEvent}
                    onHide={() => setEventDetailsModalShow(false)}
                />
            </td>
            {/* <td>{event.line_items}</td> */}
        </tr>
    )
}