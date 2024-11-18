"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { currencyFormatter, dateFormatter } from "@/lib/utils"
import { ColumnDef } from "@tanstack/react-table"

// This type is used to define the shape of our data.
// You can use a Zod schema here if you want.
export type LineItemColumn = {
    date: number;
    amount: number;
    description: string;
    responsible_party: string;
    payment_method: string;
    id: string;
}

export const columns: ColumnDef<LineItemColumn>[] = [
    {
        id: "select",
        header: ({ table }) => (
            <Checkbox
                checked={
                    table.getIsAllPageRowsSelected() ||
                    (table.getIsSomePageRowsSelected() && "indeterminate")
                }
                onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                aria-label="Select all"
            />
        ),
        cell: ({ row }) => (
            <Checkbox
                checked={row.getIsSelected()}
                onCheckedChange={(value) => row.toggleSelected(!!value)}
                aria-label="Select row"
            />
        ),
        enableSorting: false,
        enableHiding: false,
    },
    {
        accessorKey: "date",
        header: "Date",
        enableSorting: true,
        cell: ({ row }) => {
            const dateInMillis = parseFloat(row.getValue("date")) * 1000
            const formatted = dateFormatter.format(dateInMillis)
            return <div className="font-medium">{formatted}</div>
        },
    },
    {
        accessorKey: "amount",
        header: "Amount",
        enableSorting: true,
        cell: ({ row }) => {
            const amount = parseFloat(row.getValue("amount"))
            const formatted = currencyFormatter.format(amount)
            return <div className="text-right font-medium">{formatted}</div>
        },
    },
    {
        accessorKey: "description",
        header: "Description",
        enableSorting: false,
    },
    {
        accessorKey: "responsible_party",
        header: "Responsible Party",
        enableSorting: false,
    },
    {
        accessorKey: "payment_method",
        header: "Payment Method",
        enableSorting: false,
    },
]
