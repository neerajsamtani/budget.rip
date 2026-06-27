import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Body, H1 } from "@/components/ui/typography";
import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { Option } from "../components/Autocomplete";
import { EditEventContent } from "../components/EventDetailsModal";
import LineItem, { LineItemCard } from "../components/LineItem";
import { PageContainer } from "../components/ui/layout";
import { LineItemInterface } from "../contexts/LineItemsContext";
import { useCategories, useDeleteEvent, useEvent, useEventLineItems, useLineItems, useTags, useUpdateEvent } from "../hooks/useApi";
import { calculateEventTotal } from "../utils/eventHelpers";
import { CurrencyFormatter, DateFormatter } from "../utils/formatters";
import { showErrorToast, showSuccessToast } from "../utils/toast-helpers";
import { Tag } from "../components/TagsField";

function uniqueValues(values: Array<string | undefined>) {
    return Array.from(new Set(values.filter(Boolean) as string[]));
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="space-y-1">
            <dt className="text-sm font-medium text-foreground">{label}</dt>
            <dd className="text-sm text-muted-foreground break-words">{children}</dd>
        </div>
    );
}

function LinkedLineItems({ lineItems, isLoading, error }: { lineItems: LineItemInterface[]; isLoading: boolean; error: unknown }) {
    if (isLoading) {
        return (
            <div className="flex justify-center py-8">
                <Spinner size="md" className="text-muted-foreground" />
            </div>
        );
    }

    if (error) {
        return <div className="p-4 text-center text-destructive">Error loading line items. Please try again.</div>;
    }

    if (lineItems.length === 0) {
        return <div className="p-4 text-center text-muted-foreground">No linked line items found</div>;
    }

    return (
        <>
            <div className="md:hidden rounded-xl bg-white shadow-sm border overflow-hidden">
                {lineItems.map(lineItem => (
                    <LineItemCard
                        key={lineItem.id}
                        lineItem={lineItem}
                        showCheckBox={false}
                        isChecked={false}
                        handleToggle={() => { }}
                        amountStatus={lineItem.amount < 0 ? "success" : "warning"}
                    />
                ))}
            </div>
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
    );
}

export default function EventDetailPage() {
    const { eventId = "" } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const listPath = `/events${location.search}`;

    const { data: event, isLoading: isLoadingEvent, error: eventError } = useEvent(eventId);
    const { data: lineItemsForEvent = [], isLoading: isLoadingLineItemsForEvent, error: lineItemsError } = useEventLineItems(eventId);

    const [isEditing, setIsEditing] = useState(false);
    const [name, setName] = useState("");
    const [category, setCategory] = useState("");
    const [tags, setTags] = useState<Tag[]>([]);
    const [overrideDate, setOverrideDate] = useState("");
    const [isDuplicateTransaction, setIsDuplicateTransaction] = useState(false);
    const [editingLineItemIds, setEditingLineItemIds] = useState<string[]>([]);

    const deleteEventMutation = useDeleteEvent();
    const updateEventMutation = useUpdateEvent();
    const { data: existingTags, isLoading: isLoadingTags } = useTags();
    const { data: categories = [], isLoading: isLoadingCategories, isError: isCategoriesError } = useCategories();
    const { data: unreviewedLineItems = [] } = useLineItems({ onlyLineItemsToReview: true, enabled: isEditing });

    useEffect(() => {
        if (!event) return;
        setName(event.name);
        setCategory(event.category);
        setTags((event.tags || []).map((tagName, index) => ({ id: `existing-${index}`, text: tagName })));
        setOverrideDate("");
        setIsDuplicateTransaction(event.is_duplicate_transaction || false);
        setEditingLineItemIds(event.line_items);
    }, [event]);

    const currentLineItems = useMemo(() => {
        const fromEvent = lineItemsForEvent.filter(lineItem => editingLineItemIds.includes(lineItem.id));
        const fromUnreviewed = unreviewedLineItems.filter(lineItem => editingLineItemIds.includes(lineItem.id));
        return [...fromEvent, ...fromUnreviewed];
    }, [lineItemsForEvent, unreviewedLineItems, editingLineItemIds]);

    const availableLineItems = useMemo(() => {
        const removedFromEvent = lineItemsForEvent.filter(lineItem => !editingLineItemIds.includes(lineItem.id));
        const unreviewed = unreviewedLineItems.filter(lineItem => !editingLineItemIds.includes(lineItem.id));
        return [...removedFromEvent, ...unreviewed];
    }, [lineItemsForEvent, unreviewedLineItems, editingLineItemIds]);

    const tagOptions: Option[] = (existingTags || [])
        .filter(tag => !tags.some(selectedTag => selectedTag.text === tag.name))
        .map(tag => ({ value: tag.id, label: tag.name }));

    const lineItemOptions: Option[] = availableLineItems.map(lineItem => ({
        value: lineItem.id,
        label: `${lineItem.description} - ${DateFormatter.format(lineItem.date * 1000)} (${CurrencyFormatter.format(Math.abs(lineItem.amount))})`,
    }));

    const amountStatus = event && event.amount > 0 ? "warning" : "success";
    const total = useMemo(
        () => calculateEventTotal(isEditing ? currentLineItems : lineItemsForEvent, isDuplicateTransaction),
        [currentLineItems, lineItemsForEvent, isDuplicateTransaction, isEditing]
    );
    const disableSave = !name || !category || category === "All" || editingLineItemIds.length === 0;
    const paymentMethods = uniqueValues(lineItemsForEvent.map(lineItem => lineItem.payment_method));
    const responsibleParties = uniqueValues(lineItemsForEvent.map(lineItem => lineItem.responsible_party));

    const cancelEditing = () => {
        if (!event) return;
        setName(event.name);
        setCategory(event.category);
        setTags((event.tags || []).map((tagName, index) => ({ id: `existing-${index}`, text: tagName })));
        setOverrideDate("");
        setIsDuplicateTransaction(event.is_duplicate_transaction || false);
        setEditingLineItemIds(lineItemsForEvent.map(lineItem => lineItem.id));
        setIsEditing(false);
    };

    const saveChanges = () => {
        if (!event) return;
        if (disableSave) {
            showErrorToast(new Error("Please fill in all required fields and ensure at least one line item"));
            return;
        }

        updateEventMutation.mutate({
            eventId: event.id,
            name,
            category,
            line_items: editingLineItemIds,
            date: overrideDate || undefined,
            is_duplicate_transaction: isDuplicateTransaction,
            tags: tags.map(tag => tag.text),
        }, {
            onSuccess: () => {
                showSuccessToast(name, "Updated Event");
                setIsEditing(false);
            },
            onError: (error) => {
                showErrorToast(error);
            }
        });
    };

    const deleteEvent = () => {
        if (!event) return;
        deleteEventMutation.mutate(event.id, {
            onSuccess: () => {
                showSuccessToast(event.name, "Deleted Event");
                navigate(listPath);
            },
            onError: (error) => {
                showErrorToast(error);
            }
        });
    };

    if (isLoadingEvent) {
        return (
            <PageContainer>
                <div className="space-y-6">
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-12 w-80" />
                    <Skeleton className="h-64 w-full" />
                </div>
            </PageContainer>
        );
    }

    if (eventError || !event) {
        return (
            <PageContainer>
                <div className="space-y-4">
                    <Button asChild variant="ghost" size="sm">
                        <Link to={listPath}>
                            <ArrowLeft className="h-4 w-4" />
                            Events
                        </Link>
                    </Button>
                    <div className="rounded-xl border bg-white p-6">
                        <H1>Event not found</H1>
                        <Body className="text-muted-foreground">This event could not be loaded.</Body>
                    </div>
                </div>
            </PageContainer>
        );
    }

    return (
        <PageContainer>
            <div className="space-y-6">
                <Button asChild variant="ghost" size="sm">
                    <Link to={listPath}>
                        <ArrowLeft className="h-4 w-4" />
                        Events
                    </Link>
                </Button>

                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-3">
                        <div className="flex flex-wrap items-center gap-3">
                            <H1>{event.name}</H1>
                            <StatusBadge status={amountStatus}>{CurrencyFormatter.format(Math.abs(event.amount))}</StatusBadge>
                            <Badge className="bg-muted text-foreground border hover:bg-muted">{event.category}</Badge>
                            {event.tags?.map(tag => (
                                <Badge key={tag} className="bg-primary text-white px-2 py-1">{tag}</Badge>
                            ))}
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)}>
                            <Pencil className="h-4 w-4" />
                            Edit
                        </Button>
                        <Button variant="destructive" size="sm" onClick={deleteEvent} disabled={deleteEventMutation.isPending}>
                            <Trash2 className="h-4 w-4" />
                            Delete
                        </Button>
                    </div>
                </div>

                {isEditing ? (
                    <div className="rounded-xl border bg-white p-4 md:p-6">
                        <EditEventContent
                            name={name}
                            setName={setName}
                            category={category}
                            setCategory={setCategory}
                            categories={categories}
                            isLoadingCategories={isLoadingCategories}
                            isCategoriesError={isCategoriesError}
                            tags={tags}
                            tagOptions={tagOptions}
                            isLoadingTags={isLoadingTags}
                            onRemoveTag={(tagId) => setTags(tags.filter(tag => tag.id !== tagId))}
                            onAddTag={(option) => {
                                if (!tags.some(tag => tag.text === option.label)) {
                                    setTags([...tags, { id: option.value, text: option.label }]);
                                }
                            }}
                            overrideDate={overrideDate}
                            setOverrideDate={setOverrideDate}
                            isDuplicateTransaction={isDuplicateTransaction}
                            setIsDuplicateTransaction={setIsDuplicateTransaction}
                            currentLineItems={currentLineItems}
                            availableLineItems={availableLineItems}
                            lineItemOptions={lineItemOptions}
                            isLoadingLineItemsForEvent={isLoadingLineItemsForEvent}
                            onRemoveLineItem={(lineItemId) => setEditingLineItemIds(prev => prev.filter(id => id !== lineItemId))}
                            onAddLineItem={(lineItemId) => {
                                if (!editingLineItemIds.includes(lineItemId)) {
                                    setEditingLineItemIds(prev => [...prev, lineItemId]);
                                }
                            }}
                            total={total}
                            disableSave={disableSave}
                            isSaving={updateEventMutation.isPending}
                            isMobile={false}
                            titleAsDialog={false}
                            onCancel={cancelEditing}
                            onSave={saveChanges}
                        />
                    </div>
                ) : (
                    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
                        <main className="space-y-6">
                            <section className="space-y-3">
                                <h2 className="text-xl font-semibold text-foreground">Linked line items</h2>
                                <LinkedLineItems
                                    lineItems={lineItemsForEvent}
                                    isLoading={isLoadingLineItemsForEvent}
                                    error={lineItemsError}
                                />
                            </section>
                        </main>

                        <aside className="space-y-3">
                            <h2 className="text-xl font-semibold text-foreground">Details</h2>
                            <div className="rounded-xl border bg-white p-4 md:p-5">
                                <dl className="space-y-4">
                                    <DetailRow label="Event ID">{event.id}</DetailRow>
                                    <DetailRow label="Date">{DateFormatter.format(event.date * 1000)}</DetailRow>
                                    <DetailRow label="Category">{event.category}</DetailRow>
                                    <DetailRow label="Tags">{event.tags?.length ? event.tags.join(", ") : "-"}</DetailRow>
                                    <DetailRow label="Duplicate transaction">{event.is_duplicate_transaction ? "Yes" : "No"}</DetailRow>
                                    <DetailRow label="Line items">{lineItemsForEvent.length}</DetailRow>
                                    <DetailRow label="Payment methods">{paymentMethods.length ? paymentMethods.join(", ") : "-"}</DetailRow>
                                    <DetailRow label="Responsible parties">{responsibleParties.length ? responsibleParties.join(", ") : "-"}</DetailRow>
                                </dl>
                            </div>
                        </aside>
                    </div>
                )}
            </div>
        </PageContainer>
    );
}
