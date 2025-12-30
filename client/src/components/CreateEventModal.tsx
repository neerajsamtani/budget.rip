import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResponsiveDialog, useIsMobile } from "@/components/ui/responsive-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CATEGORIES } from '@/constants/categories';
import React, { useEffect, useState } from 'react';
import { Body } from "../components/ui/typography";
import { useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { FormField, useField } from '../hooks/useField';
import { CurrencyFormatter } from '../utils/formatters';
import defaultNameCleanup from '../utils/stringHelpers';
import { showSuccessToast, showErrorToast } from '../utils/toast-helpers';
import { calculateEventTotal } from '../utils/eventHelpers';
import { useCreateEvent, useTags, useEvaluateEventHints } from '../hooks/useApi';
import { Option } from './Autocomplete';
import { Tag, TagsField } from './TagsField';

export default function CreateEventModal({ show, onHide }: { show: boolean, onHide: () => void }) {

  const { lineItems } = useLineItems();
  const lineItemsDispatch = useLineItemsDispatch();
  const createEventMutation = useCreateEvent();

  const selectedLineItems = (lineItems || []).filter(lineItem => lineItem.isSelected);
  const selectedLineItemIds = selectedLineItems.map(lineItem => lineItem.id);

  // Fetch prefill suggestion from server when line items are selected
  const { data: prefillSuggestion, isLoading: isLoadingHints, isError: isHintsError } = useEvaluateEventHints(
    selectedLineItemIds,
    selectedLineItemIds.length > 0
  );

  useEffect(() => {
    // Wait for hints to finish loading before prefilling
    if (isLoadingHints) return;

    if (!show && selectedLineItems.length > 0) {
      if (isHintsError) {
        showErrorToast("Failed to load event hints. Using default name.");
      }
      if (prefillSuggestion) {
        name.setCustomValue(prefillSuggestion.name)
        if (prefillSuggestion.category) {
          category.setCustomValue(prefillSuggestion.category)
        }
      } else {
        // Fall back to default name cleanup (also handles error case)
        name.setCustomValue(defaultNameCleanup(selectedLineItems[0].description))
      }
    } else if (!show) {
      name.setEmpty()
      category.setEmpty()
    }
    // If we add name or category here, it will cause an infinite render loop
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedLineItems, show, prefillSuggestion, isLoadingHints, isHintsError])

  const name = useField<string>("text", "" as string)
  const category = useField("select", "All" as string)
  const date = useField<string>("date", "" as string)
  const isDuplicateTransaction = useField<boolean>("checkbox", false)
  const [tags, setTags] = useState<Tag[]>([]);
  const { data: existingTags, isLoading: isLoadingTags } = useTags();

  const tagOptions: Option[] = (existingTags || [])
    .filter(tag => !tags.some(t => t.text === tag.name))
    .map(tag => ({ value: tag.id, label: tag.name }));

  const handleTagSelect = (option: Option) => {
    if (!tags.some(tag => tag.text === option.label)) {
      setTags([...tags, { id: option.value, text: option.label }]);
    }
  };

  const disableSubmit = name.value === "" || category.value === "" || category.value === "All"

  const total = React.useMemo(() => {
    return calculateEventTotal(selectedLineItems, isDuplicateTransaction.value);
  }, [selectedLineItems, isDuplicateTransaction.value]);


  const closeModal = () => {
    name.setEmpty()
    category.setEmpty()
    date.setEmpty()
    setTags([])
    isDuplicateTransaction.setCustomValue(false);
    onHide()
  }

  const removeTag = (tagId: string) => {
    setTags(tags.filter(tag => tag.id !== tagId));
  };

  const createEvent = (name: FormField<string>, category: FormField<string>) => {
    const newEvent = {
      name: name.value,
      category: category.value,
      date: date.value || undefined,
      line_items: selectedLineItemIds,
      is_duplicate_transaction: isDuplicateTransaction.value,
      tags: tags.map(tag => tag.text)
    }
    createEventMutation.mutate(newEvent, {
      onSuccess: (response: { name?: string }) => {
        closeModal()
        lineItemsDispatch({
          type: 'remove_line_items',
          lineItemIds: selectedLineItemIds
        })
        showSuccessToast(response.name || newEvent.name, "Created Event");
      },
      onError: (error) => {
        showErrorToast(error);
      }
    });
  }

  const isMobile = useIsMobile();

  return (
    <ResponsiveDialog open={show} onOpenChange={closeModal} className={isMobile ? "" : "w-full !max-w-[42rem]"}>
      <div className="flex flex-col gap-2 pb-4 border-b border-muted">
        <h3 className="text-lg font-semibold text-foreground">New Event Details</h3>
        <p className="text-muted-foreground text-sm">
          Create a financial event from your selected transactions
        </p>
      </div>
      <div className="space-y-6 py-4">
        <div className="space-y-3">
          <Label htmlFor="event-name" className="text-sm font-medium text-foreground">
            Event Name
          </Label>
          <Input
            id="event-name"
            type={name.type}
            value={name.value}
            onChange={name.onChange}
            className="w-full"
            placeholder="Enter a descriptive name for this event"
          />
        </div>

        <div className="space-y-3">
          <Label id="category-label" className="text-sm font-medium text-foreground">
            Category
          </Label>
          <Select value={category.value} onValueChange={(value) => category.setCustomValue(value)}>
            <SelectTrigger className="w-full" aria-labelledby="category-label">
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
          id="event-tags"
          tags={tags}
          tagOptions={tagOptions}
          isLoading={isLoadingTags}
          onRemoveTag={removeTag}
          onAddTag={handleTagSelect}
        />

        <div className="space-y-3">
          <Label htmlFor="override-date-input" className="text-sm font-medium text-foreground">
            Override Date (optional)
          </Label>
          <Input
            id="override-date-input"
            type={date.type}
            value={date.value}
            onChange={date.onChange}
            className="w-full"
          />
        </div>

        <div className="flex items-center space-x-3 p-4 bg-muted rounded-lg">
          <Checkbox
            id="duplicate-transaction"
            checked={isDuplicateTransaction.value}
            onCheckedChange={() => isDuplicateTransaction.setCustomValue(!isDuplicateTransaction.value)}
            className="border-primary data-[state=checked]:bg-primary"
          />
          <div className="space-y-1">
            <Label htmlFor="duplicate-transaction" className="text-sm font-medium text-foreground cursor-pointer">
              Duplicate Transaction
            </Label>
            <Body className="text-muted-foreground text-xs">
              Check this if the transaction amount is double what it should be
            </Body>
          </div>
        </div>
      </div>

      <div className={`flex pt-4 border-t border-muted ${isMobile ? "flex-col gap-3" : "items-center justify-between"}`}>
        <div className="bg-muted px-4 py-2 rounded-lg">
          <Body className="text-sm font-medium text-foreground">
            Total: <span className="text-primary font-semibold">{CurrencyFormatter.format(total)}</span>
          </Body>
        </div>
        <div className={`flex gap-3 ${isMobile ? "flex-col" : ""}`}>
          <Button onClick={closeModal} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
            Cancel
          </Button>
          <Button
            onClick={() => createEvent(name, category)}
            disabled={disableSubmit}
            className={isMobile ? "w-full" : "min-w-[100px]"}
          >
            Create Event
          </Button>
        </div>
      </div>
    </ResponsiveDialog>
  );
}
