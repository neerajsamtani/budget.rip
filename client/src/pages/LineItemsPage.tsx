import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import React, { useState } from "react";
import LineItem, { LineItemCard } from "../components/LineItem";
import PaymentMethodFilter from "../components/PaymentMethodFilter";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import { useLineItems } from "../hooks/useApi";

export default function LineItemsPage() {
    const [paymentMethod, setPaymentMethod] = useState("All")

    const { data: lineItems = [], isLoading, error } = useLineItems({ paymentMethod })

    return (
        <PageContainer>
            <PageHeader>
                <H1>Line Items</H1>
                <Body className="text-muted-foreground">
                    Browse all your transaction line items with filtering options
                </Body>
            </PageHeader>

            <div className="space-y-6">
                <div className="flex flex-col sm:flex-row gap-4">
                    <PaymentMethodFilter paymentMethod={paymentMethod} setPaymentMethod={setPaymentMethod} />
                </div>

                {isLoading ? (
                    <Body className="text-center text-muted-foreground py-8">
                        Loading line items...
                    </Body>
                ) : error ? (
                    <Body className="text-center text-destructive py-8">
                        Error loading line items. Please try again.
                    </Body>
                ) : lineItems.length > 0 ? (
                    <>
                        {/* Mobile card layout */}
                        <div className="md:hidden rounded-xl bg-white shadow-sm border overflow-hidden">
                            {lineItems.map(lineItem => (
                                <LineItemCard
                                    key={lineItem.id}
                                    lineItem={lineItem}
                                    showCheckBox={false}
                                    isChecked={false}
                                    handleToggle={() => {}}
                                    amountStatus={lineItem.amount < 0 ? 'success' : 'warning'}
                                />
                            ))}
                        </div>

                        {/* Desktop table layout */}
                        <div className="hidden md:block">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Date</TableHead>
                                        <TableHead>Payment Method</TableHead>
                                        <TableHead>Description</TableHead>
                                        <TableHead>Party</TableHead>
                                        <TableHead className="text-right">Amount</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {lineItems.map(lineItem => (
                                        <LineItem key={lineItem.id} lineItem={lineItem} />
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </>
                ) : (
                    <Body className="text-center text-muted-foreground py-8">
                        No Line Items found
                    </Body>
                )}
            </div>
        </PageContainer>
    )
}