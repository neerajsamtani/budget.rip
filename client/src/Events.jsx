import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import Event from "./Event";
import CategoryFilter from "./CategoryFilter";
import MonthFilter from "./MonthFilter";
import axios from "axios";

export default function Events() {

    const [events, setEvents] = useState([])
    const [total, setTotal] = useState(0)
    const [category, setCategory] = useState("All")
    const [month, setMonth] = useState("All")

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axios.get(`${REACT_APP_API_ENDPOINT}api/events`, { params: {
            "category": category,
            "month": month
        }})
        .then(response => {
            setEvents(response.data.data)
            setTotal(response.data.total)
        })
        .catch(error => console.log(error));
    }, [month, category])

    return(
        <div>
            <h1>Events</h1>
            <p>Total: ${total}</p>
            <CategoryFilter category={category} setCategory={setCategory} />
            <MonthFilter month={month} setMonth={setMonth} />
            {events && 
            <Table striped bordered hover>
                <thead>
                    <tr>
                    <th>Date</th>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                {events.map(event => 
                    <Event key={event._id} event={event} />
                )}
                </tbody>
            </Table>
            }
            {/* {events && JSON.stringify(events, null, 2)} */}
        </div>
    )
}