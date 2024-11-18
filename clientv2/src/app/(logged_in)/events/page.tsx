"use client"

import { DataTable } from "@/components/data-table/data-table"
import { CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getEvents } from "@/lib/serverData"
import { createClient } from "@/utils/supabase/client"
import { useEffect, useState } from "react"
import { EventColumn, columns } from "./columns"

type FilterableColumn = {
    id: string
    options: {
        label: string
        value: string
    }[]
}

export default function EventsPage() {
    const [events, setEvents] = useState<EventColumn[]>([])
    const [filterableColumns, setFilterableColumns] = useState<FilterableColumn[]>([])
    const supabaseClient = createClient()

    useEffect(() => {
        const fetchData = async () => {
            const fetchedEvents = await getEvents(supabaseClient)
            setEvents(fetchedEvents)

            const categories = fetchedEvents.map((event) => event.category)
            const uniqueCategories = Array.from(new Set(categories))

            setFilterableColumns([
                {
                    id: "category",
                    options: uniqueCategories.map((category) => ({
                        label: category,
                        value: category,
                    })),
                },
            ])
        }

        fetchData()
    }, [supabaseClient])

    return (
        <div className="xl:col-span-2 text-card-foreground">
            <CardHeader className="flex flex-row items-center">
                <div className="grid gap-2">
                    <CardTitle>Events</CardTitle>
                    <CardDescription>Recent events.</CardDescription>
                </div>
            </CardHeader>
            <CardContent>
                <DataTable
                    columns={columns}
                    data={events}
                    filterableColumns={filterableColumns}
                />
            </CardContent>
        </div>
    )
}