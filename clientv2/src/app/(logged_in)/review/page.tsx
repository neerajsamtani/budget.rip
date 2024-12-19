"use client"

import { DataTable } from "@/components/data-table/data-table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getLineItemsToReview } from "@/lib/serverData"
import { Database, LineItemInterface } from "@/lib/types"
import { FilterableColumn } from "@/types"
import { createClient } from "@/utils/supabase/client"
import { Table } from "@tanstack/react-table"
import React from "react"
import { columns } from "./columns"
import CreateEvent from "./create-event"

export default function ReviewPage() {
    const supabaseClient = createClient()
    const [lineItems, setLineItems] = React.useState<LineItemInterface[]>([])
    const [selectedRows, setSelectedRows] = React.useState<Database['public']['Tables']['line_items']['Row'][]>([])

    React.useEffect(() => {
        const fetchLineItems = async () => {
            const lineItems = await getLineItemsToReview(supabaseClient)
            setLineItems(lineItems)
        }

        fetchLineItems()
    }, [supabaseClient])

    const onTableUpdate = React.useCallback((updatedTable: Table<Database['public']['Tables']['line_items']['Row']>) => {
        const newSelectedRows = updatedTable.getSelectedRowModel().rows.map((row) => row.original)
        setSelectedRows(newSelectedRows)
    }, [])

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
                        ToolbarButton={<CreateEvent selectedRows={selectedRows} />}
                        onTableUpdate={onTableUpdate}
                    />
                </CardContent>
            </Card>
        </div>
    )
}