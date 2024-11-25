import { DataTable } from "@/components/data-table/data-table"
import { CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getEvents } from "@/lib/serverData"
import { FilterableColumn } from "@/types"
import { createClient } from "@/utils/supabase/server"
import { columns } from "./columns"

export default async function EventsPage() {
    const supabaseClient = createClient()
    const events = await getEvents(supabaseClient)

    const categories = events.map((event) => event.category)
    const uniqueCategories = Array.from(new Set(categories))

    const filterableColumns: FilterableColumn[] = [
        {
            id: "category",
            options: uniqueCategories.map((category) => ({
                label: category,
                value: category,
            })),
        },
    ]

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