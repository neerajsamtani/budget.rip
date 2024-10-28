import React, { useEffect, useState } from "react";
import { Table, Form, Row, Col, InputGroup, Badge } from "react-bootstrap";
import { DateTime } from "luxon";
import Event, { EventInterface } from "../components/Event";
import CategoryFilter, { Category } from "../components/CategoryFilter";
import MonthFilter from "../components/MonthFilter";
import YearFilter from "../components/YearFilter";
import axiosInstance from "../utils/axiosInstance";

export default function EventsPage() {

    // Events for the selected month and year are fetched from the DB
    // Category filtering is done on the frontend

    const now = DateTime.now()

    const [events, setEvents] = useState<EventInterface[]>([])
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
        axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/events`, {
            params: {
                "start_time": start_time.toUnixInteger(),
                "end_time": end_time.toUnixInteger()
            }
        })
            .then(response => {
                setEvents(response.data.data)
                setTotal(response.data.total.toFixed(2) * -1)
            })
            .catch(error => console.log(error));
    }, [month, year])

    const matchCategory = (event: EventInterface) => category === "All" || category === event.category

    const calculateSpending = (events: EventInterface[]) => {
        var sum = 0;
        if (events.length > 0) {
            events.forEach((e) => {
                if (e["category"] !== "Income" && e["category"] !== "Rent" && matchCategory(e)) {
                    sum += e["amount"]
                }
            });
        }
        return sum.toFixed(2);
    }

    return (
        <div>
            <h1>Events</h1>
            <Form>
                <Row>
                    <Col>
                        <CategoryFilter category={category as Category} setCategory={setCategory} />
                    </Col>
                    <Col>
                        <MonthFilter month={month} setMonth={setMonth} />
                    </Col>
                    <Col>
                        <YearFilter year={year} setYear={setYear} />
                    </Col>
                    <Col>
                        <InputGroup className="mb-3">
                            <InputGroup.Text>Net Income</InputGroup.Text>
                            <InputGroup.Text>${total}</InputGroup.Text>
                        </InputGroup>
                    </Col>
                    <Col>
                        <InputGroup className="mb-3">
                            <InputGroup.Text>Spending w/o Rent</InputGroup.Text>
                            <InputGroup.Text>${calculateSpending(events)}</InputGroup.Text>
                        </InputGroup>
                    </Col>
                </Row>
            </Form>

            <Table striped bordered hover>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Amount</th>
                        <th>Tags</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {events.length > 0 ?
                        events
                            .filter(event => matchCategory(event))
                            .map(event => (
                                <tr key={event._id}>
                                    <Event event={event} />
                                </tr>
                            ))
                        :
                        <tr>
                            <td colSpan={6} className="text-center">
                                No events found
                            </td>
                        </tr>
                    }
                </tbody>
            </Table>
        </div>
    )
}
