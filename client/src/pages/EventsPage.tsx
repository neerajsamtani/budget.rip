import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Category } from "@/constants/categories";
import { CurrencyFormatter } from "@/utils/formatters";
import { DateTime } from "luxon";
import React, { useEffect, useState } from "react";
import CategoryFilter from "../components/CategoryFilter";
import Event, { EventInterface } from "../components/Event";
import MonthFilter from "../components/MonthFilter";
import TagsFilter from "../components/TagsFilter";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { StatusBadge } from "../components/ui/status-badge";
import { Body, H1 } from "../components/ui/typography";
import YearFilter, { type Year } from "../components/YearFilter";
import axiosInstance from "../utils/axiosInstance";
import { showErrorToast } from "../utils/toast-helpers";

export default function EventsPage() {

    // Events for the selected month and year are fetched from the DB
    // Category filtering is done on the frontend

    const now = DateTime.utc()

    const [events, setEvents] = useState<EventInterface[]>([])
    const [category, setCategory] = useState("All")
    const [month, setMonth] = useState(now.monthLong)
    const [year, setYear] = useState(String(now.year))
    const [tagFilter, setTagFilter] = useState<string>('');

    useEffect(() => {
        let start_time, end_time;
        if (month !== "All") {
            start_time = DateTime.fromFormat(`${month} ${year}`, "LLLL yyyy", { zone: 'utc' })
            end_time = start_time.endOf("month")
        } else {
            start_time = DateTime.fromFormat(`${year}`, "yyyy", { zone: 'utc' })
            end_time = start_time.endOf("year")
        }
        axiosInstance.get('api/events', {
            params: {
                "start_time": start_time.toUnixInteger(),
                "end_time": end_time.toUnixInteger()
            }
        })
            .then(response => {
                setEvents(response.data.data)
            })
            .catch(showErrorToast);
    }, [month, year])

    const matchCategory = (event: EventInterface) => category === "All" || category === event.category

    const calculateSpending = (events: EventInterface[]) => {
        const filteredEvents = events
            .filter(event =>
                matchCategory(event) &&
                matchTags(event) &&
                event.category !== "Rent" &&
                event.category !== "Income" &&
                event.category !== "Investment"
            );
        const sum = filteredEvents.reduce((acc, event) => acc + event.amount, 0);
        return sum;
    }

    const matchTags = (event: EventInterface) => {
        if (!tagFilter) return true;
        if (!event.tags) return false;
        return event.tags.some(tag =>
            tag.toLowerCase().includes(tagFilter.toLowerCase())
        );
    }

    const calculateCashFlowWithFilters = (events: EventInterface[]) => {
        const filteredEvents = events.filter(event => matchCategory(event) && matchTags(event));
        const sum = filteredEvents.reduce((acc, event) => acc + event.amount, 0);
        return sum;
    }

    const cashFlowWithFilters = calculateCashFlowWithFilters(events);
    const spending = calculateSpending(events);

    return (
        <PageContainer>
            <PageHeader>
                <H1>Events</H1>
                <Body className="text-muted-foreground">
                    View and analyze your financial events and transactions
                </Body>
            </PageHeader>

            <div className="space-y-6">
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <CategoryFilter category={category as Category} setCategory={setCategory} />
                        <MonthFilter month={month} setMonth={setMonth} />
                        <YearFilter year={year as Year} setYear={setYear} />
                        <TagsFilter tagFilter={tagFilter} setTagFilter={setTagFilter} />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-muted rounded-lg p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                            <Body className="font-medium">Cash Flow in {' '}
                                {month && month !== 'All' ? month : ''} {year}
                                {category !== 'All' ? ` (${category})` : ''}:</Body>
                            <StatusBadge status={cashFlowWithFilters < 0 ? 'success' : 'warning'}>
                                {CurrencyFormatter.format(Math.abs(cashFlowWithFilters))}
                            </StatusBadge>
                        </div>
                        <div className="bg-muted rounded-lg p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                            <Body className="font-medium">Spending:</Body>
                            <StatusBadge status={spending <= 0 ? 'success' : 'warning'}>
                                {CurrencyFormatter.format(Math.abs(spending))}
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
                                    <TableRow key={event.id}>
                                        <Event event={event} />
                                    </TableRow>
                                ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center text-muted-foreground">
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
