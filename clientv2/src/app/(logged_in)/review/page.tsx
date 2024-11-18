import { DataTable } from "@/components/data-table/data-table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getLineItemsToReview } from "@/lib/serverData"
import { createClient } from "@/utils/supabase/server"
import { columns } from "./columns"

export default async function ReviewPage() {
    const supabaseClient = createClient()
    const line_items = await getLineItemsToReview(supabaseClient)

    return (
        <div className="flex flex-col gap-4">
            <Card
                className="xl:col-span-2" x-chunk="dashboard-01-chunk-4"
            >
                <CardHeader className="flex flex-row items-center">
                    <div className="grid gap-2">
                        <CardTitle>Transactions</CardTitle>
                        <CardDescription>
                            Recent transactions to review.
                        </CardDescription>
                    </div>
                </CardHeader>
                <CardContent>
                    <DataTable columns={columns} data={line_items} />
                </CardContent>
            </Card>
        </div>
    )
}