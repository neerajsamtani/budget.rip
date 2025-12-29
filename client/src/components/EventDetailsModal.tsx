import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResponsiveDialog, ResponsiveDialogDescription, ResponsiveDialogTitle, useIsMobile } from "@/components/ui/responsive-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CATEGORIES } from '@/constants/categories';
import React, { useEffect, useMemo, useState } from 'react';
import { Body } from "../components/ui/typography";
import { LineItemInterface } from '../contexts/LineItemsContext';
import { useDeleteEvent, useLineItems, useTags, useUpdateEvent } from '../hooks/useApi';
import { CurrencyFormatter, DateFormatter } from '../utils/formatters';
import { showErrorToast, showSuccessToast } from '../utils/toast-helpers';
import { AutoComplete, Option } from './Autocomplete';
import { EventInterface } from './Event';
import LineItem, { LineItemCard } from './LineItem';
import { Tag, TagsField } from './TagsField';
import { Spinner } from "./ui/spinner";

interface ViewEventContentProps {
  event: EventInterface;
  lineItemsForEvent: LineItemInterface[];
  isLoadingLineItemsForEvent: boolean;
  isMobile: boolean;
  onEdit: () => void;
  onDelete: () => void;
}

function ViewEventContent({ event, lineItemsForEvent, isLoadingLineItemsForEvent, isMobile, onEdit, onDelete }: ViewEventContentProps) {
  return (
    <>
      <div className="flex flex-col gap-2 pb-4 border-b border-muted">
        <ResponsiveDialogTitle className="text-foreground">{event.name}</ResponsiveDialogTitle>
        <ResponsiveDialogDescription className="text-muted-foreground">
          Category: <span className="font-medium text-primary">{event.category}</span>
        </ResponsiveDialogDescription>
      </div>
      <div className="space-y-6 py-4 overflow-y-auto max-h-[60vh]">
        {isMobile ? (
          <div className="rounded-xl bg-muted/50 border overflow-hidden">
            {isLoadingLineItemsForEvent ? (
              <div className="flex justify-center items-center p-4">
                <Spinner size="sm" />
              </div>
            ) : lineItemsForEvent.map(lineItem => (
              <LineItemCard
                key={lineItem.id}
                lineItem={lineItem}
                showCheckBox={false}
                isChecked={false}
                handleToggle={() => { }}
                amountStatus={lineItem.amount < 0 ? 'success' : 'warning'}
              />
            ))}
          </div>
        ) : (
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
                {isLoadingLineItemsForEvent ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-8 text-center">
                      <div className="flex justify-center items-center w-full">
                        <Spinner size="sm" />
                      </div>
                    </TableCell>
                  </TableRow>
                ) : lineItemsForEvent.map(lineItem =>
                  <LineItem key={lineItem.id} lineItem={lineItem} />
                )}
              </TableBody>
            </Table>
          </div>
        )}
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
      </div>
      <div className={`flex pt-4 border-t border-muted gap-3 ${isMobile ? "flex-col" : "justify-end"}`}>
        <Button onClick={onEdit} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
          Edit
        </Button>
        <Button onClick={onDelete} variant="destructive" className={isMobile ? "w-full" : "min-w-[100px]"}>
          Delete
        </Button>
      </div>
    </>
  );
}

interface EditEventContentProps {
  name: string;
  setName: (name: string) => void;
  category: string;
  setCategory: (category: string) => void;
  tags: Tag[];
  tagOptions: Option[];
  isLoadingTags: boolean;
  onRemoveTag: (tagId: string) => void;
  onAddTag: (option: Option) => void;
  overrideDate: string;
  setOverrideDate: (date: string) => void;
  isDuplicateTransaction: boolean;
  setIsDuplicateTransaction: (value: boolean) => void;
  currentLineItems: LineItemInterface[];
  availableLineItems: LineItemInterface[];
  lineItemOptions: Option[];
  isLoadingLineItemsForEvent: boolean;
  onRemoveLineItem: (id: string) => void;
  onAddLineItem: (id: string) => void;
  total: number;
  disableSave: boolean;
  isSaving: boolean;
  isMobile: boolean;
  onCancel: () => void;
  onSave: () => void;
}

function EditEventContent({
  name, setName,
  category, setCategory,
  tags, tagOptions, isLoadingTags, onRemoveTag, onAddTag,
  overrideDate, setOverrideDate,
  isDuplicateTransaction, setIsDuplicateTransaction,
  currentLineItems, availableLineItems, lineItemOptions,
  isLoadingLineItemsForEvent,
  onRemoveLineItem, onAddLineItem,
  total, disableSave, isSaving, isMobile,
  onCancel, onSave
}: EditEventContentProps) {
  return (
    <>
      <div className="flex flex-col gap-2 pb-4 border-b border-muted">
        <ResponsiveDialogTitle className="text-foreground">Edit Event</ResponsiveDialogTitle>
        <ResponsiveDialogDescription className="text-muted-foreground">
          Modify event details and line items
        </ResponsiveDialogDescription>
      </div>
      <div className="space-y-6 pt-4 pb-4 px-1 -mx-1 overflow-y-auto max-h-[60vh]">
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
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="w-full" aria-labelledby="edit-category-label">
              <SelectValue placeholder="Select a category" />
            </SelectTrigger>
            <SelectContent className="bg-white border">
              {CATEGORIES.map(cat => (
                <SelectItem key={cat} value={cat}>
                  {cat}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <TagsField
          id="edit-event-tags"
          tags={tags}
          tagOptions={tagOptions}
          isLoading={isLoadingTags}
          onRemoveTag={onRemoveTag}
          onAddTag={onAddTag}
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
                onValueChange={(option) => onAddLineItem(option.value)}
                isLoading={false}
                allowCreate={false}
                clearOnSelect={true}
              />
            </div>
          )}
          {isLoadingLineItemsForEvent ? (
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
                    onClick={() => onRemoveLineItem(lineItem.id)}
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

      <div className={`flex pt-4 border-t border-muted ${isMobile ? "flex-col gap-3" : "items-center justify-between"}`}>
        <div className="bg-muted px-4 py-2 rounded-lg">
          <Body className="text-sm font-medium text-foreground">
            Total: <span className="text-primary font-semibold">{CurrencyFormatter.format(total)}</span>
          </Body>
        </div>
        <div className={`flex gap-3 ${isMobile ? "flex-col" : ""}`}>
          <Button onClick={onCancel} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
            Cancel
          </Button>
          <Button
            onClick={onSave}
            disabled={disableSave || isSaving}
            className={isMobile ? "w-full" : "min-w-[100px]"}
          >
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>
    </>
  );
}

export default function EventDetailsModal({ show, event, lineItemsForEvent, isLoadingLineItemsForEvent, onHide }:
  { show: boolean, event: EventInterface, lineItemsForEvent: LineItemInterface[], isLoadingLineItemsForEvent: boolean, onHide: () => void }) {

  const [isEditing, setIsEditing] = useState(false);

  // Form state for edit mode
  const [name, setName] = useState(event.name);
  const [category, setCategory] = useState(event.category);
  const [tags, setTags] = useState<Tag[]>([]);
  const [overrideDate, setOverrideDate] = useState('');
  const [isDuplicateTransaction, setIsDuplicateTransaction] = useState(event.is_duplicate_transaction || false);
  const [editingLineItemIds, setEditingLineItemIds] = useState<string[]>([]);

  const deleteEventMutation = useDeleteEvent();
  const updateEventMutation = useUpdateEvent();
  const isMobile = useIsMobile();
  const { data: existingTags, isLoading: isLoadingTags } = useTags();
  const { data: unreviewedLineItems = [] } = useLineItems({ onlyLineItemsToReview: true, enabled: isEditing });

  // Reset form state when event changes or when entering edit mode
  useEffect(() => {
    if (show) {
      setName(event.name);
      setCategory(event.category);
      setTags((event.tags || []).map((tagName, index) => ({ id: `existing-${index}`, text: tagName })));
      setOverrideDate('');
      setIsDuplicateTransaction(event.is_duplicate_transaction || false);
      setEditingLineItemIds(event.line_items);
    }
  }, [show, event]);

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setIsEditing(false);
      onHide();
    }
  };

  const deleteEvent = () => {
    deleteEventMutation.mutate(event.id, {
      onSuccess: () => {
        showSuccessToast(event.name, "Deleted Event");
        onHide();
      },
      onError: (error) => {
        showErrorToast(error);
      }
    });
  }

  const startEditing = () => {
    setEditingLineItemIds(lineItemsForEvent.map(li => li.id));
    setIsEditing(true);
  };

  const cancelEditing = () => {
    // Reset to original values
    setName(event.name);
    setCategory(event.category);
    setTags((event.tags || []).map((tagName, index) => ({ id: `existing-${index}`, text: tagName })));
    setOverrideDate('');
    setIsDuplicateTransaction(event.is_duplicate_transaction || false);
    setEditingLineItemIds(lineItemsForEvent.map(li => li.id));
    setIsEditing(false);
  };

  const saveChanges = () => {
    if (!name || !category || category === 'All' || editingLineItemIds.length === 0) {
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
        onHide();
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

  // Line items currently in the event during editing (from both original event and newly added unreviewed items)
  const currentLineItems = useMemo(() => {
    const fromEvent = lineItemsForEvent.filter(li => editingLineItemIds.includes(li.id));
    const fromUnreviewed = unreviewedLineItems.filter(li => editingLineItemIds.includes(li.id));
    return [...fromEvent, ...fromUnreviewed];
  }, [lineItemsForEvent, unreviewedLineItems, editingLineItemIds]);

  // Line items that can be added (unreviewed + any that were removed from this event)
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
    if (items.length === 0) return 0;
    if (isDuplicateTransaction) {
      return items[0].amount;
    }
    return items.reduce((sum, item) => sum + item.amount, 0);
  }, [currentLineItems, lineItemsForEvent, isDuplicateTransaction, isEditing]);

  const disableSave = !name || !category || category === 'All' || editingLineItemIds.length === 0;

  return (
    <ResponsiveDialog open={show} onOpenChange={handleOpenChange} className={isMobile ? "" : "w-full !max-w-[56rem]"}>
      {isEditing ? (
        <EditEventContent
          name={name}
          setName={setName}
          category={category}
          setCategory={setCategory}
          tags={tags}
          tagOptions={tagOptions}
          isLoadingTags={isLoadingTags}
          onRemoveTag={removeTag}
          onAddTag={handleTagSelect}
          overrideDate={overrideDate}
          setOverrideDate={setOverrideDate}
          isDuplicateTransaction={isDuplicateTransaction}
          setIsDuplicateTransaction={setIsDuplicateTransaction}
          currentLineItems={currentLineItems}
          availableLineItems={availableLineItems}
          lineItemOptions={lineItemOptions}
          isLoadingLineItemsForEvent={isLoadingLineItemsForEvent}
          onRemoveLineItem={removeLineItem}
          onAddLineItem={addLineItem}
          total={total}
          disableSave={disableSave}
          isSaving={updateEventMutation.isPending}
          isMobile={isMobile}
          onCancel={cancelEditing}
          onSave={saveChanges}
        />
      ) : (
        <ViewEventContent
          event={event}
          lineItemsForEvent={lineItemsForEvent}
          isLoadingLineItemsForEvent={isLoadingLineItemsForEvent}
          isMobile={isMobile}
          onEdit={startEditing}
          onDelete={deleteEvent}
        />
      )}
    </ResponsiveDialog>
  );
}
