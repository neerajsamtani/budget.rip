import { cn } from "@/lib/utils"
import {
    ArrowDownIcon,
    ArrowUpIcon,
    CaretSortIcon,
} from "@radix-ui/react-icons"
import { flexRender, Header } from "@tanstack/react-table"
import { Button } from "../ui/button"

interface DataTableColumnHeaderProps<TData, TValue>
    extends React.HTMLAttributes<HTMLDivElement> {
    header: Header<TData, TValue>
}

export function DataTableColumnHeader<TData, TValue>({
    header,
    className,
}: DataTableColumnHeaderProps<TData, TValue>) {
    if (!header.column.getCanSort()) {
        return <div className={cn(className)}>{flexRender(header.column.columnDef.header, {
            column: header.column,
            header: header,
            table: header.getContext().table,
        })}</div>
    }

    const handleSort = () => {
        const currentSort = header.column.getIsSorted()
        if (currentSort === false) {
            header.column.toggleSorting(true) // desc
        } else if (currentSort === "desc") {
            header.column.toggleSorting(false) // asc
        } else {
            header.column.clearSorting() // remove sorting
        }
    }

    return (
        <Button
            variant="ghost"
            size="sm"
            className={cn("-ml-3 h-8 data-[state=open]:bg-accent", className)}
            onClick={handleSort}
        >
            <span>{flexRender(header.column.columnDef.header, {
                column: header.column,
                header: header,
                table: header.getContext().table,
            })}</span>
            {header.column.getIsSorted() === "desc" ? (
                <ArrowDownIcon className="ml-2 h-4 w-4" />
            ) : header.column.getIsSorted() === "asc" ? (
                <ArrowUpIcon className="ml-2 h-4 w-4" />
            ) : (
                <CaretSortIcon className="ml-2 h-4 w-4" />
            )}
        </Button>
    )
}