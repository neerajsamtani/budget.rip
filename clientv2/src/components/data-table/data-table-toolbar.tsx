"use client"

import { Cross2Icon } from "@radix-ui/react-icons"
import { Table } from "@tanstack/react-table"

import { Button } from "../ui/button"

import pluralize from 'pluralize'
import { DataTableFacetedFilter } from "./data-table-faceted-filter"
import { DataTableViewOptions } from "./data-table-view-options"

interface DataTableToolbarProps<TData> {
    table: Table<TData>
    filterableColumns?: {
        id: string
        options: {
            label: string
            value: string
        }[]
    }[]
}

export function DataTableToolbar<TData>({
    table,
    filterableColumns = [],
}: DataTableToolbarProps<TData>) {
    const isFiltered = table.getState().columnFilters.length > 0

    return (
        <div className="flex items-center justify-between p-1">
            <div className="flex flex-1 items-center space-x-2">
                {filterableColumns.map((column) => (
                    <DataTableFacetedFilter
                        key={column.id}
                        column={table.getColumn(column.id)}
                        title={pluralize(column.id)}
                        options={column.options}
                    />
                ))}
                {isFiltered && (
                    <Button
                        variant="ghost"
                        onClick={() => {
                            table.resetColumnFilters()
                        }}
                        className="h-8 px-2 lg:px-3"
                    >
                        Reset
                        <Cross2Icon className="ml-2 h-4 w-4" />
                    </Button>
                )}
            </div>
            <DataTableViewOptions table={table} />
        </div>
    )
}