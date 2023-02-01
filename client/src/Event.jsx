import React, { useState } from "react";
import { Button } from "react-bootstrap";
import EventDetailsModal from "./EventDetailsModal";
import axios from "axios";

export default function Event({event}) {
    const longEnUSFormatter = new Intl.DateTimeFormat('en-US', {
        year:  'numeric',
        month: 'short',
        day:   'numeric',
    });
    const readableDate = longEnUSFormatter.format(event.date * 1000);

    const [eventDetailsModalShow, setEventDetailsModalShow] = useState(false);
    const [lineItems, setLineItems] = useState([])

    const showEventDetails = () => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axios.get(`${REACT_APP_API_ENDPOINT}api/line_items_for_event/${event._id}`)
        .then(response => {
            setLineItems(response.data.data)
        })
        .then(() => {
            setEventDetailsModalShow(true)
        })
        .catch(error => console.log(error));
    }

    // February 14, 2020
    return(
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
                        lineItems={lineItems}
                        onHide={() => setEventDetailsModalShow(false)}
                    />
                    </td>
                    {/* <td>{event.line_items}</td> */}
                </tr>
    )
}