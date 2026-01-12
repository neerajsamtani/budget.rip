import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
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

                {/* Mobile card layout */}
                <div className="md:hidden">
                    <div className="rounded-xl bg-white shadow-sm border overflow-hidden">
                        {isLoading ? (
                            <div className="flex justify-center py-8">
                                <Spinner size="md" className="text-muted-foreground" />
                            </div>
                        ) : error ? (
                            <div className="p-4 text-center text-destructive">
                                Error loading line items. Please try again.
                            </div>
                        ) : lineItems.length > 0 ? (
                            lineItems.map(lineItem => (
                                <LineItemCard
                                    key={lineItem.id}
                                    lineItem={lineItem}
                                    showCheckBox={false}
                                    isChecked={false}
                                    handleToggle={() => { }}
                                    amountStatus={lineItem.amount < 0 ? 'success' : 'warning'}
                                />
                            ))
                        ) : (
                            <div className="p-4 text-center text-muted-foreground">
                                No Line Items found
                            </div>
                        )}
                    </div>
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
                                <TableHead>Info</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center py-8">
                                        <Spinner size="md" className="text-muted-foreground mx-auto" />
                                    </TableCell>
                                </TableRow>
                            ) : error ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-destructive">
                                        Error loading line items. Please try again.
                                    </TableCell>
                                </TableRow>
                            ) : lineItems.length > 0 ? (
                                lineItems.map(lineItem => (
                                    <LineItem key={lineItem.id} lineItem={lineItem} />
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                                        No Line Items found
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </div>
            </div>
        </PageContainer>
    )
}