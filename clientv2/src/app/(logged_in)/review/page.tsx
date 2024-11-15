import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { getLineItemsToReview } from "@/lib/serverData"
import { ArrowUpRight, CircleUser, Plus } from "lucide-react"
import Link from "next/link"
import { LineItemColumn, columns } from "./columns"
import { DataTable } from "@/components/data-table/data-table"

export default async function ReviewPage() {
    const line_items = await getLineItemsToReview()

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