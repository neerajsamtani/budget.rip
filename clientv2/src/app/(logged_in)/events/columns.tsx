"use client"

import { Button } from "@/components/ui/button"
import { category_to_icon_component, currencyFormatter, dateFormatter } from "@/lib/utils"
import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown } from "lucide-react"

// This type is used to define the shape of our data.
// You can use a Zod schema here if you want.
export type EventColumn = {
    date: number;
    amount: number;
    name: string;
    category: string;
    id: string;
}

export const columns: ColumnDef<EventColumn>[] = [
    {
        accessorKey: "date",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    Date
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            )
        },
        cell: ({ row }) => {
            const dateInMillis = parseFloat(row.getValue("date")) * 1000
            const formatted = dateFormatter.format(dateInMillis)
            return <div className="font-medium">{formatted}</div>
        },
    },
    {
        accessorKey: "amount",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    <div className="text-right">Amount</div>
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            )
        },
        cell: ({ row }) => {
            const amount = parseFloat(row.getValue("amount"))
            const formatted = currencyFormatter.format(amount)
            return <div className="text-right font-medium">{formatted}</div>
        },
    },
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        accessorKey: "category",
        header: "Category",
        filterFn: (row, id, value: string[]) => {
            return value.includes(row.getValue(id))
        },
        cell: ({ row }) => {
            const category = row.getValue("category") as string
            return (
                <div className="flex items-center gap-2">
                    {category_to_icon_component(category)}
                    <p className="text-md font-medium leading-none">
                        {category}
                    </p>
                </div>
            )
        },
    },
]
