import { DateTime } from "luxon";
import React, { useEffect, useState } from "react";
import { Col, Form, InputGroup, Row, Table } from "react-bootstrap";
import CategoryFilter, { Category } from "../components/CategoryFilter";
import Event, { EventInterface } from "../components/Event";
import MonthFilter from "../components/MonthFilter";
import TagsFilter from "../components/TagsFilter";
import YearFilter from "../components/YearFilter";
import axiosInstance from "../utils/axiosInstance";

export default function EventsPage() {

    // Events for the selected month and year are fetched from the DB
    // Category filtering is done on the frontend

    const now = DateTime.utc()

    const [events, setEvents] = useState<EventInterface[]>([])
    const [category, setCategory] = useState("All")
    const [month, setMonth] = useState(now.monthLong)
    const [year, setYear] = useState(now.year)
    const [tagFilter, setTagFilter] = useState<string>('');

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        var start_time, end_time;
        if (month !== "All") {
            start_time = DateTime.fromFormat(`${month} ${year}`, "LLLL yyyy", { zone: 'utc' })
            end_time = start_time.endOf("month")
        } else {
            start_time = DateTime.fromFormat(`${year}`, "yyyy", { zone: 'utc' })
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
            })
            .catch(error => console.log(error));
    }, [month, year])

    const matchCategory = (event: EventInterface) => category === "All" || category === event.category

    const calculateSpending = (events: EventInterface[]) => {
        const filteredEvents = events
            .filter(event =>
                matchCategory(event) &&
                matchTags(event) &&
                event.category !== "Rent" &&
                event.category !== "Income"
            );
        const sum = filteredEvents.reduce((acc, event) => acc + event.amount, 0);
        return sum.toFixed(2);
    }

    const matchTags = (event: EventInterface) => {
        if (!tagFilter) return true;
        if (!event.tags) return false;
        return event.tags.some(tag =>
            tag.toLowerCase().includes(tagFilter.toLowerCase())
        );
    }

    const calculateNetIncome = (events: EventInterface[]) => {
        const filteredEvents = events.filter(event => matchCategory(event) && matchTags(event));
        const sum = filteredEvents.reduce((acc, event) => acc + event.amount, 0);
        return sum.toFixed(2);
    }

    return (
        <div>
            <h1>Events</h1>
            <Form className="mb-4">
                <Row className="mb-3">
                    <Col md={3}>
                        <CategoryFilter category={category as Category} setCategory={setCategory} />
                    </Col>
                    <Col md={3}>
                        <MonthFilter month={month} setMonth={setMonth} />
                    </Col>
                    <Col md={3}>
                        <YearFilter year={year} setYear={setYear} />
                    </Col>
                    <Col md={3}>
                        <TagsFilter tagFilter={tagFilter} setTagFilter={setTagFilter} />
                    </Col>
                </Row>
                <Row>
                    <Col md={6}>
                        <InputGroup>
                            <InputGroup.Text>Net Income</InputGroup.Text>
                            <InputGroup.Text>${calculateNetIncome(events)}</InputGroup.Text>
                        </InputGroup>
                    </Col>
                    <Col md={6}>
                        <InputGroup>
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
                            .filter(event => matchCategory(event) && matchTags(event))
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
