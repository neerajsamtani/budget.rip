import Filter from "@/components/Filter"
import { CATEGORIES } from "@/lib/types"

export default async function ComponentsPage() {
    return <pre><Filter paramName="category" options={CATEGORIES} defaultValue="All" /></pre>
}