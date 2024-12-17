"use client"

import { TrendingUp } from "lucide-react"
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts"

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import {
    ChartConfig,
    ChartContainer,
    ChartLegend,
    ChartLegendContent,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart"

export const description = "A stacked bar chart with a legend"

interface BarChartProps {
    chartData: Record<string, number | string>[];
    title: string;
    description: string;
    categories: string[];
    xAxisKey: string;
    xAxisFormatter?: (value: string) => string;
}

export function CustomBarChart({
    chartData,
    title,
    description,
    categories,
    xAxisKey,
    xAxisFormatter = (value) => value
}: BarChartProps) {
    const chartConfig = {
        total_amount: {
            label: "Amount",
            color: "hsl(var(--chart-1))",
        },
    } satisfies ChartConfig

    return (
        <Card>
            <CardHeader>
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
                <ChartContainer config={chartConfig}>
                    <BarChart accessibilityLayer data={chartData}>
                        <CartesianGrid vertical={false} />
                        <XAxis
                            dataKey={xAxisKey}
                            tickLine={false}
                            tickMargin={10}
                            axisLine={false}
                            tickFormatter={xAxisFormatter}
                        />
                        <ChartTooltip labelFormatter={xAxisFormatter} content={<ChartTooltipContent />} />
                        <ChartLegend content={<ChartLegendContent />} />
                        {categories.map((category, index) => (
                            <Bar
                                key={category}
                                dataKey={category}
                                fill={`hsl(var(--chart-${(index % 20) + 1}))`}
                                stackId="a"
                                radius={0}
                            />
                        ))}
                    </BarChart>
                </ChartContainer>
            </CardContent>
            <CardFooter className="flex-col items-start gap-2 text-sm">
                <div className="flex gap-2 font-medium leading-none">
                    Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
                </div>
                <div className="leading-none text-muted-foreground">
                    Showing total visitors for the last 6 months
                </div>
            </CardFooter>
        </Card>
    )
}
