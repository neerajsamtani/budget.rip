import Filter from "@/components/Filter"
import { CATEGORIES, MONTHS, YEARS } from "@/lib/constants"

export default async function ComponentsPage() {
    return (
        <pre>
            <Filter paramName="category" options={CATEGORIES} defaultValue="All" />
            <Filter paramName="month" options={MONTHS} defaultValue="All" />
            <Filter paramName="year" options={YEARS} defaultValue="All" />
        </pre>)
}