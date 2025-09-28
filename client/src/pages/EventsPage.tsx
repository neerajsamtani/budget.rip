import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { H1, Body } from "../components/ui/typography";
import { StatusBadge } from "../components/ui/status-badge";
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

    const netIncome = calculateNetIncome(events);
    const spending = calculateSpending(events);

    return (
        <PageContainer>
            <PageHeader>
                <H1>Events</H1>
                <Body className="text-[#6B7280]">
                    View and analyze your financial events and transactions
                </Body>
            </PageHeader>

            <div className="space-y-6">
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <CategoryFilter category={category as Category} setCategory={setCategory} />
                        <MonthFilter month={month} setMonth={setMonth} />
                        <YearFilter year={year} setYear={setYear} />
                        <TagsFilter tagFilter={tagFilter} setTagFilter={setTagFilter} />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-[#F5F5F5] rounded-lg p-4 flex items-center justify-between">
                            <Body className="font-medium">Net Income:</Body>
                            <StatusBadge status={parseFloat(netIncome) >= 0 ? 'success' : 'error'}>
                                ${netIncome}
                            </StatusBadge>
                        </div>
                        <div className="bg-[#F5F5F5] rounded-lg p-4 flex items-center justify-between">
                            <Body className="font-medium">Spending w/o Rent:</Body>
                            <StatusBadge status={parseFloat(spending) <= 0 ? 'success' : 'warning'}>
                                ${spending}
                            </StatusBadge>
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
                        {events.length > 0 ? (
                            events
                                .filter(event => matchCategory(event) && matchTags(event))
                                .map(event => (
                                    <TableRow key={event._id}>
                                        <Event event={event} />
                                    </TableRow>
                                ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center text-[#6B7280]">
                                    No events found
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </PageContainer>
    )
}
