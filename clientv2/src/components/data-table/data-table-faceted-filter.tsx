import { CheckIcon, Cross2Icon, PlusCircledIcon } from "@radix-ui/react-icons"
import { Column } from "@tanstack/react-table"
import * as React from "react"

import { cn, toSentenceCase } from "@/lib/utils"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
    CommandSeparator,
} from "../ui/command"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "../ui/popover"
import { Separator } from "../ui/separator"

interface DataTableFacetedFilterProps<TData, TValue> {
    column?: Column<TData, TValue>
    title?: string
    options: {
        label: string
        value: string
        icon?: React.ComponentType<{ className?: string }>
    }[]
}

export function DataTableFacetedFilter<TData, TValue>({
    column,
    title,
    options,
}: DataTableFacetedFilterProps<TData, TValue>) {
    const facets = column?.getFacetedUniqueValues()
    const selectedValues = new Set(column?.getFilterValue() as string[])

    const removeValue = (valueToRemove: string) => {
        selectedValues.delete(valueToRemove)
        const filterValues = Array.from(selectedValues)
        column?.setFilterValue(
            filterValues.length ? filterValues : undefined
        )
    }

    // Sort options, keeping "All" at the top if it exists, and selected items next
    const sortedOptions = [...options].sort((a, b) => {
        if (a.value === 'all') return -1;
        if (b.value === 'all') return 1;
        const aSelected = selectedValues.has(a.value);
        const bSelected = selectedValues.has(b.value);
        if (aSelected && !bSelected) return -1;
        if (!aSelected && bSelected) return 1;
        return a.label.localeCompare(b.label);
    });

    return (
        <Popover>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className="h-8 border-dashed bg-background hover:bg-accent hover:text-accent-foreground"
                >
                    {selectedValues?.size > 0 ? null : (
                        <PlusCircledIcon className="mr-2 h-4 w-4" />
                    )}
                    {toSentenceCase(title)}
                    {selectedValues?.size > 0 && (
                        <>
                            <Separator orientation="vertical" className="mx-2 h-4" />
                            <Badge
                                variant="secondary"
                                className="rounded-sm px-1 font-normal lg:hidden"
                            >
                                {selectedValues.size}
                            </Badge>
                            <div className="hidden space-x-1 lg:flex">
                                {selectedValues.size > 2 ? (
                                    <Badge
                                        variant="secondary"
                                        className="rounded-sm px-1 font-normal"
                                    >
                                        {selectedValues.size} selected
                                    </Badge>
                                ) : (
                                    options
                                        .filter((option) => selectedValues.has(option.value))
                                        .map((option) => (
                                            <Badge
                                                variant="secondary"
                                                key={option.value}
                                                className="rounded-sm px-1 font-normal flex items-center gap-1"
                                            >
                                                {option.label}
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="h-auto p-0 px-0.5 hover:bg-transparent"
                                                    onClick={(e) => {
                                                        e.stopPropagation()
                                                        removeValue(option.value)
                                                    }}
                                                >
                                                    <Cross2Icon className="h-3 w-3 text-muted-foreground hover:text-foreground" />
                                                </Button>
                                            </Badge>
                                        ))
                                )}
                            </div>
                        </>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent
                className="w-[200px] p-0"
                align="start"
                side="bottom"
            >
                <Command className="rounded-lg border shadow-md">
                    <CommandInput
                        placeholder={`Search ${toSentenceCase(title)}...`}
                        className="h-9 px-3 border-none focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 rounded-none"
                    />
                    <CommandList>
                        <CommandEmpty>No results found.</CommandEmpty>
                        {selectedValues.size > 0 && (
                            <CommandGroup heading="Selected" className="p-1.5">
                                {sortedOptions
                                    .filter(option => selectedValues.has(option.value))
                                    .map((option) => (
                                        <CommandItem
                                            key={option.value}
                                            onSelect={() => {
                                                selectedValues.delete(option.value)
                                                const filterValues = Array.from(selectedValues)
                                                column?.setFilterValue(
                                                    filterValues.length ? filterValues : undefined
                                                )
                                            }}
                                            className="flex items-center gap-2 px-2 py-1.5 aria-selected:bg-accent"
                                        >
                                            <div
                                                className={cn(
                                                    "flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                                    "bg-primary text-primary-foreground"
                                                )}
                                            >
                                                <CheckIcon className={cn("h-3 w-3")} />
                                            </div>
                                            {option.icon && (
                                                <option.icon className="h-4 w-4 text-muted-foreground shrink-0" />
                                            )}
                                            <span>{option.label}</span>
                                            {facets?.get(option.value) && (
                                                <span className="ml-auto flex h-4 w-4 items-center justify-center font-mono text-xs text-muted-foreground">
                                                    {facets.get(option.value)}
                                                </span>
                                            )}
                                        </CommandItem>
                                    ))}
                            </CommandGroup>
                        )}
                        <CommandGroup heading="All Options" className="p-1.5">
                            {sortedOptions
                                .filter(option => !selectedValues.has(option.value))
                                .map((option) => {
                                    const isSelected = selectedValues.has(option.value)
                                    return (
                                        <CommandItem
                                            key={option.value}
                                            onSelect={() => {
                                                if (isSelected) {
                                                    selectedValues.delete(option.value)
                                                } else {
                                                    selectedValues.add(option.value)
                                                }
                                                const filterValues = Array.from(selectedValues)
                                                column?.setFilterValue(
                                                    filterValues.length ? filterValues : undefined
                                                )
                                            }}
                                            className="flex items-center gap-2 px-2 py-1.5 aria-selected:bg-accent"
                                        >
                                            <div
                                                className={cn(
                                                    "flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                                    isSelected
                                                        ? "bg-primary text-primary-foreground"
                                                        : "opacity-50 [&_svg]:invisible"
                                                )}
                                            >
                                                <CheckIcon className={cn("h-3 w-3")} />
                                            </div>
                                            {option.icon && (
                                                <option.icon className="h-4 w-4 text-muted-foreground shrink-0" />
                                            )}
                                            <span>{option.label}</span>
                                            {facets?.get(option.value) && (
                                                <span className="ml-auto flex h-4 w-4 items-center justify-center font-mono text-xs text-muted-foreground">
                                                    {facets.get(option.value)}
                                                </span>
                                            )}
                                        </CommandItem>
                                    )
                                })}
                        </CommandGroup>
                        {selectedValues.size > 0 && (
                            <>
                                <CommandSeparator />
                                <CommandGroup>
                                    <CommandItem
                                        onSelect={() => column?.setFilterValue(undefined)}
                                        className="justify-center text-center text-sm px-2 py-1.5"
                                    >
                                        Clear filters
                                    </CommandItem>
                                </CommandGroup>
                            </>
                        )}
                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    )
}