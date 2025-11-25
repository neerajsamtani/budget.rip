import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Category } from "@/constants/categories";
import { CurrencyFormatter } from "@/utils/formatters";
import { ChevronDown, ChevronUp, Filter } from "lucide-react";
import { DateTime } from "luxon";
import React, { useState } from "react";
import CategoryFilter from "../components/CategoryFilter";
import Event, { EventCard, EventInterface } from "../components/Event";
import MonthFilter from "../components/MonthFilter";
import TagsFilter from "../components/TagsFilter";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { StatusBadge } from "../components/ui/status-badge";
import { Body, H1 } from "../components/ui/typography";
import YearFilter, { type Year } from "../components/YearFilter";
import { useEvents } from "../hooks/useApi";

export default function EventsPage() {
    const now = DateTime.utc()

    const [category, setCategory] = useState("All")
    const [month, setMonth] = useState(now.monthLong)
    const [year, setYear] = useState(String(now.year))
    const [tagFilter, setTagFilter] = useState<string>('');
    const [filtersOpen, setFiltersOpen] = useState(false);

    // Calculate time range for API query
    let startTime, endTime;
    if (month !== "All") {
        const start = DateTime.fromFormat(`${month} ${year}`, "LLLL yyyy", { zone: 'utc' })
        startTime = start.toUnixInteger()
        endTime = start.endOf("month").toUnixInteger()
    } else {
        const start = DateTime.fromFormat(`${year}`, "yyyy", { zone: 'utc' })
        startTime = start.toUnixInteger()
        endTime = start.endOf("year").toUnixInteger()
    }

    const { data: events = [], isLoading, error } = useEvents(startTime, endTime)

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
    const filteredEvents = events.filter(event => matchCategory(event) && matchTags(event));

    // Count active filters
    const activeFilterCount = [
        category !== "All",
        month !== "All",
        tagFilter !== ""
    ].filter(Boolean).length;

    return (
        <PageContainer>
            <PageHeader>
                <H1>Events</H1>
                <Body className="text-muted-foreground">
                    View and analyze your financial events and transactions
                </Body>
            </PageHeader>

            <div className="space-y-4">
                {/* Mobile filters toggle */}
                <div className="md:hidden">
                    <Button
                        variant="secondary"
                        onClick={() => setFiltersOpen(!filtersOpen)}
                        className="w-full justify-between"
                    >
                        <span className="flex items-center gap-2">
                            <Filter className="h-4 w-4" />
                            Filters
                            {activeFilterCount > 0 && (
                                <span className="bg-primary text-white text-xs px-2 py-0.5 rounded-full">
                                    {activeFilterCount}
                                </span>
                            )}
                        </span>
                        {filtersOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </Button>
                </div>

                {/* Filters - collapsible on mobile, always visible on desktop */}
                <div className={`space-y-4 ${filtersOpen ? 'block' : 'hidden'} md:block`}>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                        <MonthFilter month={month} setMonth={setMonth} />
                        <YearFilter year={year as Year} setYear={setYear} />
                        <CategoryFilter category={category as Category} setCategory={setCategory} />
                        <TagsFilter tagFilter={tagFilter} setTagFilter={setTagFilter} />
                    </div>
                </div>

                {/* Summary cards */}
                <div className="grid grid-cols-2 gap-3 md:gap-4">
                    <div className="bg-muted rounded-lg p-3 md:p-4 flex items-center justify-between gap-2">
                        <Body className="font-medium text-xs md:text-base">
                            Cash Flow
                        </Body>
                        {isLoading ? (
                            <Skeleton className="h-6 w-20 bg-green-50" />
                        ) : (
                            <StatusBadge status={cashFlowWithFilters < 0 ? 'success' : 'warning'}>
                                {CurrencyFormatter.format(Math.abs(cashFlowWithFilters))}
                            </StatusBadge>
                        )}
                    </div>
                    <div className="bg-muted rounded-lg p-3 md:p-4 flex items-center justify-between gap-2">
                        <Body className="font-medium text-xs md:text-base">Spending</Body>
                        {isLoading ? (
                            <Skeleton className="h-6 w-20 bg-yellow-50" />
                        ) : (
                            <StatusBadge status={spending <= 0 ? 'success' : 'warning'}>
                                {CurrencyFormatter.format(Math.abs(spending))}
                            </StatusBadge>
                        )}
                    </div>
                </div>

                {/* Mobile card layout */}
                <div className="md:hidden">
                    <div className="rounded-xl bg-white shadow-sm border overflow-hidden">
                        {isLoading ? (
                            <div className="flex justify-center py-8">
                                <Spinner size="md" className="text-muted-foreground" />
                            </div>
                        ) : error ? (
                            <div className="p-4 text-center text-destructive">
                                Error loading events. Please try again.
                            </div>
                        ) : filteredEvents.length > 0 ? (
                            filteredEvents.map(event => (
                                <EventCard key={event.id} event={event} />
                            ))
                        ) : (
                            <div className="p-4 text-center text-muted-foreground">
                                No events found
                            </div>
                        )}
                    </div>
                </div>

                {/* Desktop table layout */}
                <div className="hidden md:block">
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
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="text-center py-8">
                                        <Spinner size="md" className="text-muted-foreground mx-auto" />
                                    </TableCell>
                                </TableRow>
                            ) : error ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="text-center text-destructive">
                                        Error loading events. Please try again.
                                    </TableCell>
                                </TableRow>
                            ) : filteredEvents.length > 0 ? (
                                filteredEvents.map(event => (
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
            </div>
        </PageContainer>
    )
}
