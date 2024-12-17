import { cn } from "@/lib/utils"
import {
    ArrowDownIcon,
    ArrowUpIcon,
    CaretSortIcon,
} from "@radix-ui/react-icons"
import { Column } from "@tanstack/react-table"
import { Button } from "../ui/button"

interface DataTableColumnHeaderProps<TData, TValue>
    extends React.HTMLAttributes<HTMLDivElement> {
    column: Column<TData, TValue>
    title: string
}

export function DataTableColumnHeader<TData, TValue>({
    column,
    title,
    className,
}: DataTableColumnHeaderProps<TData, TValue>) {
    if (!column.getCanSort()) {
        return <div className={cn(className)}>{title}</div>
    }

    const handleSort = () => {
        const currentSort = column.getIsSorted()
        if (currentSort === false) {
            column.toggleSorting(true) // desc
        } else if (currentSort === "desc") {
            column.toggleSorting(false) // asc
        } else {
            column.clearSorting() // remove sorting
        }
    }

    return (
        <Button
            variant="ghost"
            size="sm"
            className={cn("-ml-3 h-8 data-[state=open]:bg-accent", className)}
            onClick={handleSort}
        >
            <span>{title}</span>
            {column.getIsSorted() === "desc" ? (
                <ArrowDownIcon className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "asc" ? (
                <ArrowUpIcon className="ml-2 h-4 w-4" />
            ) : (
                <CaretSortIcon className="ml-2 h-4 w-4" />
            )}
        </Button>
    )
}