import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { DateTime } from "luxon";
import Event from "./Event";
import CategoryFilter from "./CategoryFilter";
import MonthFilter from "./MonthFilter";
import YearFilter from "./YearFilter";
import axios from "axios";

export default function Events() {

    const now = DateTime.now()

    const [events, setEvents] = useState([])
    const [total, setTotal] = useState(0)
    const [category, setCategory] = useState("All")
    const [month, setMonth] = useState(now.monthLong)
    const [year, setYear] = useState(now.year)

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        var start_time, end_time;
        if (month !== "All") {
            start_time = DateTime.fromFormat(`${month} ${year}`, "LLLL yyyy")
            end_time = start_time.endOf("month")
        } else {
            start_time = DateTime.fromFormat(`${year}`, "yyyy")
            end_time = start_time.endOf("year")
        }
        axios.get(`${REACT_APP_API_ENDPOINT}api/events`, { params: {
            "category": category,
            "start_time": start_time.toUnixInteger(),
            "end_time": end_time.toUnixInteger()
        }})
        .then(response => {
            setEvents(response.data.data)
            setTotal(response.data.total)
        })
        .catch(error => console.log(error));
    }, [month, year, category])

    const calculateSpending = (events) => {
        var sum = 0;
        if (events.length > 0) {
            events.forEach((e) => {
                if (e["category"] !== "Income" &&  e["category"] !== "Rent") {
                    sum += e["amount"]
                }
            });
        }
        return sum;
    }

    return(
        <div>
            <h1>Events</h1>
            <p>Total Leftover: ${total}</p>
            <p>Spending without Rent: ${calculateSpending(events)}</p>
            <CategoryFilter category={category} setCategory={setCategory} />
            <MonthFilter month={month} setMonth={setMonth} />
            <YearFilter year={year} setYear={setYear} />
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