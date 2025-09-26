import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DateTime } from "luxon";
import React, { useEffect, useState } from "react";
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
        const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
        let start_time, end_time;
        if (month !== "All") {
            start_time = DateTime.fromFormat(`${month} ${year}`, "LLLL yyyy", { zone: 'utc' })
            end_time = start_time.endOf("month")
        } else {
            start_time = DateTime.fromFormat(`${year}`, "yyyy", { zone: 'utc' })
            end_time = start_time.endOf("year")
        }
        axiosInstance.get(`${VITE_API_ENDPOINT}api/events`, {
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
            <div className="mb-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <CategoryFilter category={category as Category} setCategory={setCategory} />
                    <MonthFilter month={month} setMonth={setMonth} />
                    <YearFilter year={year} setYear={setYear} />
                    <TagsFilter tagFilter={tagFilter} setTagFilter={setTagFilter} />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center space-x-2 p-2 border rounded">
                        <span className="font-medium">Net Income:</span>
                        <span>${calculateNetIncome(events)}</span>
                    </div>
                    <div className="flex items-center space-x-2 p-2 border rounded">
                        <span className="font-medium">Spending w/o Rent:</span>
                        <span>${calculateSpending(events)}</span>
                    </div>
                </div>
            </div>

            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Tags</TableHead>
                        <TableHead>Actions</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {events.length > 0 ?
                        events
                            .filter(event => matchCategory(event) && matchTags(event))
                            .map(event => (
                                <TableRow key={event._id}>
                                    <Event event={event} />
                                </TableRow>
                            ))
                        :
                        <TableRow>
                            <TableCell colSpan={6} className="text-center">
                                No events found
                            </TableCell>
                        </TableRow>
                    }
                </TableBody>
            </Table>
        </div>
    )
}
