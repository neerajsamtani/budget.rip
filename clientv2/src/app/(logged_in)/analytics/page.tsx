"use client"

import { CustomBarChart } from "@/components/CustomBarChart"
import { CustomLineChart } from "@/components/CustomLineChart"
import DatePickerWithRange from "@/components/date-picker"
import { CATEGORIES } from "@/lib/constants"
import { getAmountPerCategoryPerMonth, getNetEarningsPerMonth } from "@/lib/serverData"
import { createClient } from "@/utils/supabase/client"
import { useSearchParams } from "next/navigation"
import { Suspense, useEffect, useState } from "react"

interface ChartDataItem {
    month: string;
    category: typeof CATEGORIES[number];
    total_amount: number;
}

const dateLabelFormatter = (value: string) =>
    `${new Date(value).toLocaleDateString('en-US', { timeZone: 'UTC', month: 'long', year: 'numeric' })}`

// Create a separate component for the analytics content
function AnalyticsContent() {
    const searchParams = useSearchParams();
    const startDate = searchParams.get(encodeURIComponent("from")) || undefined;
    const endDate = searchParams.get(encodeURIComponent("to")) || undefined;

    const [netEarningsPerMonth, setNetEarningsPerMonth] = useState<any[]>([])
    const [amountPerCategoryPerMonth, setAmountPerCategoryPerMonth] = useState<any[]>([])

    const supabaseClient = createClient()

    const processBarChartData = (data: ChartDataItem[]) => {
        const categories = CATEGORIES.filter(cat =>
            cat !== 'All' && cat !== 'Income' && cat !== 'Investment' && cat !== 'Rent'
        );

        return data.reduce((acc: Record<string, number | string>[], curr: ChartDataItem) => {
            const existingMonth = acc.find(item => item.month === curr.month);
            if (!existingMonth) {
                const newMonth: Record<string, number | string> = {
                    month: curr.month,
                    ...Object.fromEntries(categories.map(cat => [cat, 0]))
                };
                newMonth[curr.category] = curr.total_amount;
                acc.push(newMonth);
            } else {
                existingMonth[curr.category] = curr.total_amount;
            }
            return acc;
        }, []);
    }

    useEffect(() => {
        const fetchData = async () => {
            try {
                const nepm = await getNetEarningsPerMonth(supabaseClient, startDate, endDate);
                setNetEarningsPerMonth(nepm || []);
                const apcpm = await getAmountPerCategoryPerMonth(supabaseClient, startDate, endDate);
                setAmountPerCategoryPerMonth(apcpm || []);
            } catch (err) {
                console.error("Error fetching data:", err);
            }
        };

        fetchData();
    }, [endDate, startDate, supabaseClient])

    const displayCategories = CATEGORIES.filter(cat =>
        cat !== 'All' && cat !== 'Income' && cat !== 'Investment' && cat !== 'Rent'
    );

    const processedBarChartData = processBarChartData(amountPerCategoryPerMonth);

    return (
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8 border-border">
            <DatePickerWithRange />
            <div className="grid gap-4 md:gap-8 lg:grid-cols-2 xl:grid-cols-3">
                <CustomBarChart
                    title="Monthly Expenses"
                    description={`${startDate ? dateLabelFormatter(startDate) : 'Start'} - ${endDate ? dateLabelFormatter(endDate) : 'Present'}`}
                    chartData={processedBarChartData}
                    categories={displayCategories}
                    xAxisKey="month"
                    xAxisFormatter={dateLabelFormatter}
                />
                <CustomLineChart chartData={netEarningsPerMonth} />
            </div>
        </main>
    )
}

// Main page component with Suspense
export default function AnalyticsPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <AnalyticsContent />
        </Suspense>
    )
}
