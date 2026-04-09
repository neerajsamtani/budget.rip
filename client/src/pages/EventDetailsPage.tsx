import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ChevronLeft } from "lucide-react";
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AutoComplete, Option } from '../components/Autocomplete';
import LineItem from '../components/LineItem';
import { Body } from '../components/ui/typography';
import { PageContainer } from '../components/ui/layout';
import { Tag, TagsField } from '../components/TagsField';
import { LineItemInterface } from '../contexts/LineItemsContext';
import { useCategories, useDeleteEvent, useEvent, useEventLineItems, useLineItems, useTags, useUpdateEvent } from '../hooks/useApi';
import { calculateEventTotal } from '../utils/eventHelpers';
import { CurrencyFormatter, DateFormatter } from '../utils/formatters';
import { showErrorToast, showSuccessToast } from '../utils/toast-helpers';

export default function EventDetailsPage() {
    const { eventId } = useParams<{ eventId: string }>();
    const navigate = useNavigate();

    const { data: event, isLoading: isLoadingEvent, error: eventError } = useEvent(eventId!);
    const { data: lineItemsForEvent = [], isLoading: isLoadingLineItems } = useEventLineItems(eventId!);

    const [isEditing, setIsEditing] = useState(false);
    const [name, setName] = useState('');
    const [category, setCategory] = useState('');
    const [tags, setTags] = useState<Tag[]>([]);
    const [overrideDate, setOverrideDate] = useState('');
    const [isDuplicateTransaction, setIsDuplicateTransaction] = useState(false);
    const [editingLineItemIds, setEditingLineItemIds] = useState<string[]>([]);

    const deleteEventMutation = useDeleteEvent();
    const updateEventMutation = useUpdateEvent();
    const { data: existingTags, isLoading: isLoadingTags } = useTags({ enabled: isEditing });
    const { data: categories = [], isLoading: isLoadingCategories, isError: isCategoriesError } = useCategories({ enabled: isEditing });
    const { data: unreviewedLineItems = [] } = useLineItems({ onlyLineItemsToReview: true, enabled: isEditing });

    useEffect(() => {
        if (event) {
            setName(event.name);
            setCategory(event.category);
            setTags((event.tags || []).map((tagName, index) => ({ id: `existing-${index}`, text: tagName })));
            setOverrideDate('');
            setIsDuplicateTransaction(event.is_duplicate_transaction || false);
            setEditingLineItemIds(event.line_items);
        }
    }, [event]);

    const deleteEvent = () => {
        deleteEventMutation.mutate(event!.id, {
            onSuccess: () => {
                showSuccessToast(event!.name, "Deleted Event");
                navigate('/events');
            },
            onError: (error) => {
                showErrorToast(error);
            }
        });
    };

    const startEditing = () => {
        setEditingLineItemIds(lineItemsForEvent.map(li => li.id));
        setIsEditing(true);
    };

    const cancelEditing = () => {
        if (event) {
            setName(event.name);
            setCategory(event.category);
            setTags((event.tags || []).map((tagName, index) => ({ id: `existing-${index}`, text: tagName })));
            setOverrideDate('');
            setIsDuplicateTransaction(event.is_duplicate_transaction || false);
            setEditingLineItemIds(lineItemsForEvent.map(li => li.id));
        }
        setIsEditing(false);
    };

    const saveChanges = () => {
        if (!name || !category || category === 'All' || editingLineItemIds.length === 0) {
            showErrorToast(new Error("Please fill in all required fields and ensure at least one line item"));
            return;
        }

        updateEventMutation.mutate({
            eventId: event!.id,
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

    const removeLineItem = (lineItemId: string) => {
        setEditingLineItemIds(prev => prev.filter(id => id !== lineItemId));
    };

    const addLineItem = (lineItemId: string) => {
        if (!editingLineItemIds.includes(lineItemId)) {
            setEditingLineItemIds(prev => [...prev, lineItemId]);
        }
    };

    const removeTag = (tagId: string) => {
        setTags(tags.filter(tag => tag.id !== tagId));
    };

    const tagOptions: Option[] = (existingTags || [])
        .filter(tag => !tags.some(t => t.text === tag.name))
        .map(tag => ({ value: tag.id, label: tag.name }));

    const handleTagSelect = (option: Option) => {
        if (!tags.some(tag => tag.text === option.label)) {
            setTags([...tags, { id: option.value, text: option.label }]);
        }
    };

    const currentLineItems = useMemo(() => {
        const fromEvent = lineItemsForEvent.filter(li => editingLineItemIds.includes(li.id));
        const fromUnreviewed = unreviewedLineItems.filter(li => editingLineItemIds.includes(li.id));
        return [...fromEvent, ...fromUnreviewed];
    }, [lineItemsForEvent, unreviewedLineItems, editingLineItemIds]);

    const availableLineItems = useMemo(() => {
        const removedFromEvent = lineItemsForEvent.filter(li => !editingLineItemIds.includes(li.id));
        const unreviewed = unreviewedLineItems.filter(li => !editingLineItemIds.includes(li.id));
        return [...removedFromEvent, ...unreviewed];
    }, [lineItemsForEvent, unreviewedLineItems, editingLineItemIds]);

    const lineItemOptions: Option[] = availableLineItems.map(li => ({
        value: li.id,
        label: `${li.description} - ${DateFormatter.format(li.date * 1000)} (${CurrencyFormatter.format(Math.abs(li.amount))})`,
    }));

    const total = useMemo(() => {
        const items = isEditing ? currentLineItems : lineItemsForEvent;
        return calculateEventTotal(items, isDuplicateTransaction);
    }, [currentLineItems, lineItemsForEvent, isDuplicateTransaction, isEditing]);

    const disableSave = !name || !category || category === 'All' || editingLineItemIds.length === 0;

    if (isLoadingEvent) {
        return (
            <PageContainer>
                <div className="flex justify-center py-20">
                    <Spinner size="md" />
                </div>
            </PageContainer>
        );
    }

    if (eventError || !event) {
        return (
            <PageContainer>
                <Button variant="ghost" className="mb-4 -ml-6" onClick={() => navigate(-1)}>
                    <ChevronLeft className="h-4 w-4 mr-1" />Back to Events
                </Button>
                <p className="text-muted-foreground">Event not found.</p>
            </PageContainer>
        );
    }

    return (
        <PageContainer>
            <Button variant="ghost" className="mb-4 -ml-6" onClick={() => navigate(-1)}>
                <ChevronLeft className="h-4 w-4 mr-1" />Back to Events
            </Button>

            {isEditing ? (
                <div className="space-y-6">
                    <div className="flex flex-col gap-1 max-w-2xl mx-auto">
                        <h1 className="text-2xl font-semibold text-foreground">Edit Event</h1>
                        <p className="text-muted-foreground text-sm">Modify event details and line items</p>
                    </div>

                    <div className="space-y-6 max-w-2xl mx-auto">
                        <div className="space-y-3">
                            <Label htmlFor="edit-event-name" className="text-sm font-medium text-foreground">
                                Event Name
                            </Label>
                            <Input
                                id="edit-event-name"
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full"
                                placeholder="Enter a descriptive name for this event"
                            />
                        </div>

                        <div className="space-y-3">
                            <Label id="edit-category-label" className="text-sm font-medium text-foreground">
                                Category
                            </Label>
                            <Select value={category} onValueChange={setCategory} disabled={isLoadingCategories}>
                                <SelectTrigger className="w-full" aria-labelledby="edit-category-label">
                                    <SelectValue placeholder={isLoadingCategories ? "Loading..." : isCategoriesError ? "Error loading categories" : "Select a category"} />
                                </SelectTrigger>
                                <SelectContent className="bg-white border">
                                    {categories.map(cat => (
                                        <SelectItem key={cat.id} value={cat.name}>
                                            {cat.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            {isCategoriesError && (
                                <p className="text-sm text-destructive">Failed to load categories. Please refresh the page.</p>
                            )}
                        </div>

                        <TagsField
                            id="edit-event-tags"
                            tags={tags}
                            tagOptions={tagOptions}
                            isLoading={isLoadingTags}
                            onRemoveTag={removeTag}
                            onAddTag={handleTagSelect}
                        />

                        <div className="space-y-3">
                            <Label htmlFor="edit-override-date" className="text-sm font-medium text-foreground">
                                Override Date (optional)
                            </Label>
                            <Input
                                id="edit-override-date"
                                type="date"
                                value={overrideDate}
                                onChange={(e) => setOverrideDate(e.target.value)}
                                className="w-full"
                            />
                        </div>

                        <div className="flex items-center space-x-3 p-4 bg-muted rounded-lg">
                            <Checkbox
                                id="edit-duplicate-transaction"
                                checked={isDuplicateTransaction}
                                onCheckedChange={() => setIsDuplicateTransaction(!isDuplicateTransaction)}
                                className="border-primary data-[state=checked]:bg-primary"
                            />
                            <div className="space-y-1">
                                <Label htmlFor="edit-duplicate-transaction" className="text-sm font-medium text-foreground cursor-pointer">
                                    Duplicate Transaction
                                </Label>
                                <Body className="text-muted-foreground text-xs">
                                    Check this if the transaction amount is double what it should be
                                </Body>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <Label className="text-sm font-medium text-foreground">
                                Line Items ({currentLineItems.length})
                            </Label>
                            {availableLineItems.length > 0 && (
                                <div className="space-y-2">
                                    <Label className="text-sm text-muted-foreground">Add line item</Label>
                                    <AutoComplete
                                        options={lineItemOptions}
                                        placeholder="Search for line items to add..."
                                        onValueChange={(option) => addLineItem(option.value)}
                                        isLoading={false}
                                        allowCreate={false}
                                        clearOnSelect={true}
                                    />
                                </div>
                            )}
                            {isLoadingLineItems ? (
                                <div className="flex justify-center items-center p-4">
                                    <Spinner size="sm" />
                                </div>
                            ) : (
                                <div className="rounded-xl bg-muted/50 border overflow-hidden">
                                    {currentLineItems.map(lineItem => (
                                        <div key={lineItem.id} className="flex items-center justify-between p-3 border-b last:border-b-0">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-foreground truncate">{lineItem.description}</p>
                                                <p className="text-xs text-muted-foreground">
                                                    {DateFormatter.format(lineItem.date * 1000)} • {CurrencyFormatter.format(Math.abs(lineItem.amount))}
                                                </p>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => removeLineItem(lineItem.id)}
                                                className="text-destructive hover:text-destructive hover:bg-destructive/10 ml-2"
                                                disabled={currentLineItems.length <= 1}
                                            >
                                                Remove
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-muted max-w-2xl mx-auto">
                        <div className="bg-muted px-4 py-2 rounded-lg">
                            <Body className="text-sm font-medium text-foreground">
                                Total: <span className="text-primary font-semibold">{CurrencyFormatter.format(total)}</span>
                            </Body>
                        </div>
                        <div className="flex gap-3">
                            <Button onClick={cancelEditing} variant="secondary" className="min-w-[100px]">
                                Cancel
                            </Button>
                            <Button
                                onClick={saveChanges}
                                disabled={disableSave || updateEventMutation.isPending}
                                className="min-w-[100px]"
                            >
                                {updateEventMutation.isPending ? "Saving..." : "Save Changes"}
                            </Button>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="space-y-6">
                    <div className="flex flex-col gap-1">
                        <h1 className="text-2xl font-semibold text-foreground">{event.name}</h1>
                        <p className="text-muted-foreground text-sm">
                            Category: <span className="font-medium text-primary">{event.category}</span>
                        </p>
                    </div>

                    <div className="overflow-x-auto">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Date</TableHead>
                                    <TableHead>Payment Method</TableHead>
                                    <TableHead>Description</TableHead>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Amount</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoadingLineItems ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="p-8 text-center">
                                            <div className="flex justify-center items-center w-full">
                                                <Spinner size="sm" />
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ) : lineItemsForEvent.map((lineItem: LineItemInterface) => (
                                    <LineItem key={lineItem.id} lineItem={lineItem} />
                                ))}
                            </TableBody>
                        </Table>
                    </div>

                    {event.tags && event.tags.length > 0 && (
                        <div className="flex items-center gap-3">
                            <Body className="font-medium text-foreground">Tags:</Body>
                            <div className="flex flex-wrap gap-2">
                                {event.tags.map((tag, index) => (
                                    <Badge key={index} className="bg-primary text-white px-3 py-1">
                                        {tag}
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="flex pt-4 border-t border-muted gap-3 justify-end">
                        <Button onClick={startEditing} variant="secondary" className="min-w-[100px]">
                            Edit
                        </Button>
                        <Button onClick={deleteEvent} variant="destructive" className="min-w-[100px]">
                            Delete
                        </Button>
                    </div>
                </div>
            )}
        </PageContainer>
    );
}
