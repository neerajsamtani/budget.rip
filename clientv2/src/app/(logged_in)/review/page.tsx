"use client"

import { DataTable } from "@/components/data-table/data-table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getLineItemsToReview } from "@/lib/serverData"
import { createClient } from "@/utils/supabase/client"
import { useEffect, useState } from "react"
import { LineItemColumn, columns } from "./columns"

type FilterableColumn = {
    id: string
    options: {
        label: string
        value: string
    }[]
}

export default function ReviewPage() {
    const [lineItems, setLineItems] = useState<LineItemColumn[]>([])
    const [filterableColumns, setFilterableColumns] = useState<FilterableColumn[]>([])
    const supabaseClient = createClient()

    useEffect(() => {
        const fetchData = async () => {
            const fetchedLineItems = await getLineItemsToReview(supabaseClient)
            setLineItems(fetchedLineItems)

            const paymentMethods = fetchedLineItems.map((item) => item.payment_method)
            const uniquePaymentMethods = Array.from(new Set(paymentMethods))

            setFilterableColumns([
                {
                    id: "payment_method",
                    options: uniquePaymentMethods.map((method) => ({
                        label: method,
                        value: method,
                    })),
                },
            ])
        }

        fetchData()
    }, [supabaseClient])

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