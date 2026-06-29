import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageContainer } from "@/components/ui/layout";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Body, H1 } from "@/components/ui/typography";
import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { useDeleteManualTransaction, useEvent, useLineItem, usePaymentMethods, useUpdateLineItem } from "../hooks/useApi";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { showErrorToast, showSuccessToast } from "../utils/toast-helpers";

function dateInputValue(timestamp?: number) {
    if (!timestamp) return "";
    return new Date(timestamp * 1000).toISOString().slice(0, 10);
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="space-y-1">
            <dt className="text-sm font-medium text-foreground">{label}</dt>
            <dd className="text-sm text-muted-foreground break-words">{children}</dd>
        </div>
    );
}

function ActionButton({
    children,
    className,
    disabled,
    tooltip,
    ...props
}: React.ComponentProps<typeof Button> & { tooltip?: string }) {
    if (!disabled || !tooltip) {
        return (
            <Button className={className} disabled={disabled} {...props}>
                {children}
            </Button>
        );
    }

    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <span className={`inline-flex ${className || ""}`}>
                        <Button className="w-full" disabled={disabled} {...props}>
                            {children}
                        </Button>
                    </span>
                </TooltipTrigger>
                <TooltipContent>
                    <p>{tooltip}</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}

function getSafeReturnTo(value: string | null) {
    if (!value || !value.startsWith("/") || value.startsWith("//")) return undefined;
    return value;
}

function getBackLabel(path: string) {
    if (path === "/") return "Review";
    if (path.startsWith("/events/")) return "Event";
    return "Line Items";
}

export default function LineItemDetailPage() {
    const { lineItemId = "" } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const searchParams = new URLSearchParams(location.search);
    const returnTo = getSafeReturnTo(searchParams.get("returnTo"));
    searchParams.delete("returnTo");
    const lineItemsSearch = searchParams.toString();
    const lineItemsPath = `/line_items${lineItemsSearch ? `?${lineItemsSearch}` : ""}`;
    const backPath = returnTo || lineItemsPath;
    const backLabel = getBackLabel(backPath);
    const hasRouteHistory = location.key !== "default";

    const goBack = () => {
        if (hasRouteHistory) {
            navigate(-1);
            return;
        }
        navigate(backPath);
    };

    const { data: lineItem, isLoading, error } = useLineItem(lineItemId);
    const eventId = lineItem?.event_id || "";
    const { data: assignedEvent, isLoading: isLoadingAssignedEvent, error: assignedEventError } = useEvent(eventId);
    const { data: paymentMethods = [], isLoading: isLoadingPaymentMethods } = usePaymentMethods();
    const updateLineItemMutation = useUpdateLineItem();
    const deleteManualTransactionMutation = useDeleteManualTransaction();

    const [isEditing, setIsEditing] = useState(false);
    const [date, setDate] = useState("");
    const [responsibleParty, setResponsibleParty] = useState("");
    const [description, setDescription] = useState("");
    const [amount, setAmount] = useState("");
    const [paymentMethodId, setPaymentMethodId] = useState("");
    const [notes, setNotes] = useState("");

    useEffect(() => {
        if (!lineItem) return;
        setDate(dateInputValue(lineItem.date));
        setResponsibleParty(lineItem.responsible_party || "");
        setDescription(lineItem.description || "");
        setAmount(String(lineItem.amount ?? 0));
        setPaymentMethodId(lineItem.payment_method_id || "");
        setNotes(lineItem.notes || "");
    }, [lineItem]);

    if (isLoading) {
        return (
            <PageContainer>
                <div className="space-y-6">
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-12 w-96" />
                    <Skeleton className="h-64 w-full" />
                </div>
            </PageContainer>
        );
    }

    if (error || !lineItem) {
        return (
            <PageContainer>
                <div className="space-y-4">
                    <Button variant="ghost" size="sm" onClick={goBack}>
                        <ArrowLeft className="h-4 w-4" />
                        {backLabel}
                    </Button>
                    <div className="rounded-xl border bg-white p-6">
                        <H1>Line item not found</H1>
                        <Body className="text-muted-foreground">This line item could not be loaded.</Body>
                    </div>
                </div>
            </PageContainer>
        );
    }

    const amountStatus = lineItem.amount < 0 ? "success" : "warning";
    const isManual = !!lineItem.is_manual;
    const sourceLabel = lineItem.source_label || (isManual ? "Manual" : "Unknown");
    const isAssigned = !!lineItem.event_id;
    const editTooltip = isManual ? undefined : "Synced line items cannot be edited.";
    const deleteTooltip = !isManual
        ? "Synced line items cannot be deleted."
        : isAssigned
            ? "Remove this line item from its event before deleting it."
            : undefined;
    const canEdit = isManual;
    const canDelete = isManual && !isAssigned;
    const disableSave = !date || !description || !paymentMethodId || Number.isNaN(Number(amount));

    const cancelEditing = () => {
        setDate(dateInputValue(lineItem.date));
        setResponsibleParty(lineItem.responsible_party || "");
        setDescription(lineItem.description || "");
        setAmount(String(lineItem.amount ?? 0));
        setPaymentMethodId(lineItem.payment_method_id || "");
        setNotes(lineItem.notes || "");
        setIsEditing(false);
    };

    const saveChanges = () => {
        if (disableSave) {
            showErrorToast(new Error("Please fill in all required fields"));
            return;
        }

        updateLineItemMutation.mutate({
            lineItemId: lineItem.id,
            date,
            responsible_party: responsibleParty,
            description,
            amount: Number(amount),
            payment_method_id: paymentMethodId,
            notes,
        }, {
            onSuccess: () => {
                showSuccessToast(description, "Updated Line Item");
                setIsEditing(false);
            },
            onError: (mutationError) => {
                showErrorToast(mutationError);
            },
        });
    };

    const deleteLineItem = () => {
        if (!lineItem.transaction_id || !canDelete) return;

        deleteManualTransactionMutation.mutate(lineItem.transaction_id, {
            onSuccess: () => {
                showSuccessToast(lineItem.description, "Deleted Line Item");
                navigate(backPath);
            },
            onError: (mutationError) => {
                showErrorToast(mutationError);
            },
        });
    };

    return (
        <PageContainer>
            <div className="space-y-6">
                <Button variant="ghost" size="sm" onClick={goBack}>
                    <ArrowLeft className="h-4 w-4" />
                    {backLabel}
                </Button>

                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0 space-y-3">
                        <div className="flex min-w-0 flex-wrap items-center gap-2 sm:gap-3">
                            <H1 className="min-w-0 w-full break-words text-[30px] tracking-normal sm:w-auto">{lineItem.description}</H1>
                            <StatusBadge status={amountStatus}>{CurrencyFormatter.format(Math.abs(lineItem.amount))}</StatusBadge>
                            {isAssigned && (
                                <Badge className="max-w-full truncate bg-muted text-foreground border hover:bg-muted">Assigned to event</Badge>
                            )}
                        </div>
                    </div>
                    <div className="flex w-full gap-2 sm:w-auto">
                        <ActionButton
                            variant="secondary"
                            size="sm"
                            onClick={() => setIsEditing(true)}
                            disabled={!canEdit}
                            tooltip={editTooltip}
                            className="flex-1 sm:flex-none"
                        >
                            <Pencil className="h-4 w-4" />
                            Edit
                        </ActionButton>
                        <ActionButton
                            variant="destructive"
                            size="sm"
                            onClick={deleteLineItem}
                            disabled={!canDelete || deleteManualTransactionMutation.isPending}
                            tooltip={deleteTooltip}
                            className="flex-1 sm:flex-none"
                        >
                            <Trash2 className="h-4 w-4" />
                            Delete
                        </ActionButton>
                    </div>
                </div>

                {isEditing ? (
                    <div className="rounded-xl border bg-white p-4 md:p-6">
                        <div className="flex flex-col gap-2 pb-4 border-b border-muted">
                            <h2 className="text-xl font-semibold text-foreground">Edit Line Item</h2>
                            <p className="text-sm text-muted-foreground">Update this manual line item</p>
                        </div>
                        <div className="grid gap-4 py-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <Label htmlFor="line-item-date">Date</Label>
                                <Input id="line-item-date" type="date" value={date} onChange={(event) => setDate(event.target.value)} />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="line-item-payment-method">Payment Method</Label>
                                <Select value={paymentMethodId} onValueChange={setPaymentMethodId} disabled={isLoadingPaymentMethods}>
                                    <SelectTrigger id="line-item-payment-method" className="w-full">
                                        <SelectValue placeholder={isLoadingPaymentMethods ? "Loading..." : "Select payment method"} />
                                    </SelectTrigger>
                                    <SelectContent className="bg-white border">
                                        {paymentMethods.map(paymentMethod => (
                                            <SelectItem key={paymentMethod.id} value={paymentMethod.id}>
                                                {paymentMethod.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="line-item-party">Party</Label>
                                <Input id="line-item-party" value={responsibleParty} onChange={(event) => setResponsibleParty(event.target.value)} />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="line-item-amount">Amount</Label>
                                <Input id="line-item-amount" type="number" value={amount} onChange={(event) => setAmount(event.target.value)} />
                            </div>
                            <div className="space-y-2 md:col-span-2">
                                <Label htmlFor="line-item-description">Description</Label>
                                <Input id="line-item-description" value={description} onChange={(event) => setDescription(event.target.value)} />
                            </div>
                            <div className="space-y-2 md:col-span-2">
                                <Label htmlFor="line-item-notes">Notes</Label>
                                <Textarea id="line-item-notes" value={notes} onChange={(event) => setNotes(event.target.value)} />
                            </div>
                        </div>
                        <div className="flex flex-col gap-3 pt-4 border-t border-muted sm:flex-row sm:justify-end">
                            <Button variant="secondary" onClick={cancelEditing} className="w-full sm:w-auto">Cancel</Button>
                            <Button onClick={saveChanges} disabled={disableSave || updateLineItemMutation.isPending} className="w-full sm:w-auto">
                                {updateLineItemMutation.isPending ? "Saving..." : "Save Changes"}
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
                        <main className="space-y-3">
                            <h2 className="text-xl font-semibold text-foreground">Line item</h2>
                            <div className="rounded-xl border bg-white p-4 md:p-5">
                                <dl className="grid gap-4 md:grid-cols-2">
                                    <DetailRow label="Date">{DateFormatter.format(lineItem.date * 1000)}</DetailRow>
                                    <DetailRow label="Payment method">{lineItem.payment_method}</DetailRow>
                                    <DetailRow label="Party">{lineItem.responsible_party || "-"}</DetailRow>
                                    <DetailRow label="Amount">{CurrencyFormatter.format(Math.abs(lineItem.amount))}</DetailRow>
                                    <DetailRow label="Description">{lineItem.description}</DetailRow>
                                    <DetailRow label="Notes">{lineItem.notes || "-"}</DetailRow>
                                </dl>
                            </div>
                        </main>

                        <aside className="space-y-3">
                            <h2 className="text-xl font-semibold text-foreground">Details</h2>
                            <div className="rounded-xl border bg-white p-4 md:p-5">
                                <dl className="space-y-4">
                                    <DetailRow label="Event">
                                        {!isAssigned ? (
                                            "Not assigned"
                                        ) : isLoadingAssignedEvent ? (
                                            "Loading..."
                                        ) : assignedEventError || !assignedEvent ? (
                                            "Assigned event unavailable"
                                        ) : (
                                            <Link to={`/events/${assignedEvent.id}`} className="text-primary hover:underline">
                                                {assignedEvent.name}
                                            </Link>
                                        )}
                                    </DetailRow>
                                    <DetailRow label="Category">
                                        {isAssigned && isLoadingAssignedEvent ? "Loading..." : assignedEvent?.category || "-"}
                                    </DetailRow>
                                    <DetailRow label="Tags">
                                        {isAssigned && isLoadingAssignedEvent ? "Loading..." : assignedEvent?.tags?.length ? assignedEvent.tags.join(", ") : "-"}
                                    </DetailRow>
                                    <DetailRow label="Source">{sourceLabel}</DetailRow>
                                </dl>
                            </div>
                        </aside>
                    </div>
                )}
            </div>
        </PageContainer>
    );
}
