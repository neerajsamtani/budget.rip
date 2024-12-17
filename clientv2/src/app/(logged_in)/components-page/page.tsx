"use client"
import Filter, { filterInUrlParam } from "@/components/Filter";
import LineItemsTable from "@/components/LineItemsTable";
import { CATEGORIES, MONTHS, YEARS } from "@/lib/constants";
import { getPaymentMethods } from "@/lib/data";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

function ComponentsContent() {
    const searchParams = useSearchParams();

    const [paymentMethods, setPaymentMethods] = useState([]);

    const payment_method = searchParams.get(filterInUrlParam("Payment Method")) || undefined;
    const month = searchParams.get(filterInUrlParam("Month")) || undefined;
    const year = searchParams.get(filterInUrlParam("Year")) || undefined;
    const category = searchParams.get(filterInUrlParam("Category")) || undefined;

    useEffect(() => {
        const fetchPaymentMethods = async () => {
            try {
                const methods = await getPaymentMethods();
                setPaymentMethods(methods || []);
            } catch (err) {
                console.error("Error fetching payment methods:", err);
            }
        };

        fetchPaymentMethods();
    }, [payment_method, month, year]); // Empty dependency array means this effect runs once on mount

    return (
        <>
            <Filter paramName="Category" options={CATEGORIES} defaultValue="All" />
            <Filter paramName="Month" options={MONTHS} defaultValue="All" />
            <Filter paramName="Year" options={YEARS} defaultValue="All" />
            <Filter paramName="Payment Method" options={paymentMethods} defaultValue="All" />

            <p>Category: {category}</p>
            <p>Month: {month}</p>
            <p>Year: {year}</p>
            <p>Payment Method: {payment_method}</p>

            <LineItemsTable />
        </>
    )
}

export default function ComponentsPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <ComponentsContent />
        </Suspense>
    )
}