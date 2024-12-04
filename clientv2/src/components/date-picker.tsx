"use client"

import { format, isSameDay, startOfMonth, startOfYear, subDays, subYears } from "date-fns"
import { CalendarIcon } from 'lucide-react'
import * as React from "react"
import { DateRange } from "react-day-picker"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { usePathname, useRouter, useSearchParams } from "next/navigation"

const today = new Date()

const presets = [
    {
        label: "Last 7 Days",
        value: "last-7-days",
        dateRange: {
            from: subDays(today, 6),
            to: today,
        },
    },
    {
        label: "Last 30 Days",
        value: "last-30-days",
        dateRange: {
            from: subDays(today, 29),
            to: today,
        },
    },
    {
        label: "Last 90 Days",
        value: "last-90-days",
        dateRange: {
            from: subDays(today, 89),
            to: today,
        },
    },
    {
        label: "Last Year",
        value: "last-year",
        dateRange: {
            from: subYears(today, 1),
            to: today,
        },
    },
    {
        label: "Month to Date",
        value: "month-to-date",
        dateRange: {
            from: startOfMonth(today),
            to: today,
        },
    },
    {
        label: "Year to Date",
        value: "year-to-date",
        dateRange: {
            from: startOfYear(today),
            to: today,
        },
    },
]

export default function DatePickerWithRange({
    className,
}: React.HTMLAttributes<HTMLDivElement>) {
    /*
    * TODO: Add support for timezone and upgrade to the new react-day-picker
    * This component is used to select a date range for the app.
    * It uses the search params to get the date range, and the pathname to navigate to the correct page.
    */
    const [activePreset, setActivePreset] = React.useState<string | null>(null)
    const searchParams = useSearchParams()
    const pathname = usePathname()
    const { replace } = useRouter()
    const [open, setOpen] = React.useState(false)

    const dateRange = searchParams.get("from") && searchParams.get("to") ? {
        from: new Date(searchParams.get("from") || ""),
        to: new Date(searchParams.get("to") || ""),
    } : {
        from: presets[presets.length - 1].dateRange.from,
        to: presets[presets.length - 1].dateRange.to,
    }


    const handleDateRangeChange = (dateRange: DateRange | undefined) => {
        const params = new URLSearchParams(searchParams)
        if (dateRange?.from && dateRange?.to) {
            params.set("from", dateRange.from.toISOString())
            params.set("to", dateRange.to.toISOString())
        } else {
            params.delete("from")
            params.delete("to")
        }
        replace(`${pathname}?${params.toString()}`);
    }

    const handlePresetClick = (preset: typeof presets[number]) => {
        handleDateRangeChange(preset.dateRange)
        setActivePreset(preset.value)
        setOpen(false)
    }

    const handleDateSelect = (selectedDateRange: DateRange | undefined) => {
        handleDateRangeChange(selectedDateRange)
        if (selectedDateRange?.from && selectedDateRange?.to) {
            const matchingPreset = presets.find(
                (preset) =>
                    selectedDateRange?.from && selectedDateRange?.to &&
                    isSameDay(preset.dateRange.from, selectedDateRange.from) &&
                    isSameDay(preset.dateRange.to, selectedDateRange.to)
            )
            setActivePreset(matchingPreset ? matchingPreset.value : "custom")
        } else {
            setActivePreset(null)
        }
    }

    const getButtonText = () => {
        if (!dateRange?.from) {
            return "Pick a date"
        }

        if (activePreset && activePreset !== "custom") {
            return presets.find(preset => preset.value === activePreset)?.label
        }

        if (dateRange.to) {
            return `${format(dateRange.from, "LLL dd, y")} - ${format(dateRange.to, "LLL dd, y")}`
        }

        return format(dateRange.from, "LLL dd, y")
    }

    return (
        <div className={cn("grid gap-2", className)}>
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button
                        id="date"
                        variant={"outline"}
                        className={cn(
                            "w-[260px] justify-start text-left font-normal",
                            !dateRange && "text-muted-foreground"
                        )}
                    >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {getButtonText()}
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                    <div className="flex">
                        <div className="border-r p-2 space-y-1 flex flex-col">
                            {presets.map((preset) => (
                                <Button
                                    key={preset.value}
                                    onClick={() => handlePresetClick(preset)}
                                    variant={activePreset === preset.value ? "secondary" : "ghost"}
                                    className="justify-start font-normal text-sm px-2 py-1 h-auto"
                                >
                                    {preset.label}
                                </Button>
                            ))}
                            <Button
                                onClick={() => setActivePreset("custom")}
                                variant={activePreset === "custom" ? "secondary" : "ghost"}
                                className="justify-start font-normal text-sm px-2 py-1 h-auto"
                            >
                                Custom Range
                            </Button>
                        </div>
                        <div className="p-3">
                            <Calendar
                                initialFocus
                                fixedWeeks
                                showOutsideDays={false}
                                mode="range"
                                defaultMonth={dateRange?.from}
                                selected={dateRange}
                                onSelect={handleDateSelect}
                                numberOfMonths={2}
                                toMonth={today}
                                disabled={[{ after: today }]}
                            />
                        </div>
                    </div>
                </PopoverContent>
            </Popover>
        </div>
    )
}

