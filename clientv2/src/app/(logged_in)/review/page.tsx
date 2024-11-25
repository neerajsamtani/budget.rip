import { DataTable } from "@/components/data-table/data-table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getLineItemsToReview } from "@/lib/serverData"
import { FilterableColumn } from "@/types"
import { createClient } from "@/utils/supabase/client"
import { columns } from "./columns"

export default async function ReviewPage() {
    const supabaseClient = createClient()
    const lineItems = await getLineItemsToReview(supabaseClient)

    const paymentMethods = lineItems.map((item) => item.payment_method)
    const uniquePaymentMethods = Array.from(new Set(paymentMethods))

    const filterableColumns: FilterableColumn[] = [
        {
            id: "payment_method",
            options: uniquePaymentMethods.map((method) => ({
                label: method,
                value: method,
            })),
        },
    ]

    return (
        <div className="flex flex-col gap-4">
            <Card className="xl:col-span-2">
                <CardHeader className="flex flex-row items-center">
                    <div className="grid gap-2">
                        <CardTitle>Transactions</CardTitle>
                        <CardDescription>
                            Recent transactions to review.
                        </CardDescription>
                    </div>
                </CardHeader>
                <CardContent>
                    <DataTable
                        columns={columns}
                        data={lineItems}
                        filterableColumns={filterableColumns}
                    />
                </CardContent>
            </Card>
        </div>
    )
}