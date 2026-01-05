import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResponsiveDialog, useIsMobile } from "@/components/ui/responsive-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import React, { useEffect, useState } from 'react';
import { Body } from "../components/ui/typography";
import { LineItemInterface, useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { useCategories, useCreateEvent, useEvaluateEventHints, useTags } from '../hooks/useApi';
import { useField } from '../hooks/useField';
import { calculateEventTotal } from '../utils/eventHelpers';
import { CurrencyFormatter } from '../utils/formatters';
import defaultNameCleanup from '../utils/stringHelpers';
import { showErrorToast, showSuccessToast } from '../utils/toast-helpers';
import { Option } from './Autocomplete';
import { Tag, TagsField } from './TagsField';
import { Spinner } from './ui/spinner';

interface CreateEventModalContentProps {
  initialName: string;
  initialCategory: string;
  selectedLineItems: LineItemInterface[];
  selectedLineItemIds: string[];
  onClose: () => void;
  isLoadingHints: boolean;
}

/**
 * Inner component that manages form state. Uses key prop from parent to reset
 * when initial values change, eliminating the need for effects to sync state.
 */
function CreateEventModalContent({
  initialName,
  initialCategory,
  selectedLineItems,
  selectedLineItemIds,
  onClose,
  isLoadingHints,
}: CreateEventModalContentProps) {
  const lineItemsDispatch = useLineItemsDispatch();
  const createEventMutation = useCreateEvent();

  // Form fields initialize with props - when parent changes the key, this component
  // remounts with fresh state using the new initial values
  const name = useField<string>("text", initialName);
  const category = useField("select", initialCategory);
  const date = useField<string>("date", "");
  const isDuplicateTransaction = useField<boolean>("checkbox", false);
  const [tags, setTags] = useState<Tag[]>([]);

  const { data: existingTags, isLoading: isLoadingTags } = useTags();
  const { data: categories = [], isLoading: isLoadingCategories, isError: isCategoriesError } = useCategories();

  const tagOptions: Option[] = (existingTags || [])
    .filter(tag => !tags.some(t => t.text === tag.name))
    .map(tag => ({ value: tag.id, label: tag.name }));

  const handleTagSelect = (option: Option) => {
    if (!tags.some(tag => tag.text === option.label)) {
      setTags([...tags, { id: option.value, text: option.label }]);
    }
  };

  const removeTag = (tagId: string) => {
    setTags(tags.filter(tag => tag.id !== tagId));
  };

  const disableSubmit = name.value === "" || category.value === "" || category.value === "All";

  const total = React.useMemo(() => {
    return calculateEventTotal(selectedLineItems, isDuplicateTransaction.value);
  }, [selectedLineItems, isDuplicateTransaction.value]);

  const createEvent = () => {
    const newEvent = {
      name: name.value,
      category: category.value,
      date: date.value || undefined,
      line_items: selectedLineItemIds,
      is_duplicate_transaction: isDuplicateTransaction.value,
      tags: tags.map(tag => tag.text)
    };
    createEventMutation.mutate(newEvent, {
      onSuccess: (response: { name?: string }) => {
        onClose();
        lineItemsDispatch({
          type: 'remove_line_items',
          lineItemIds: selectedLineItemIds
        });
        showSuccessToast(response.name || newEvent.name, "Created Event");
      },
      onError: (error) => {
        showErrorToast(error);
      }
    });
  };

  const isMobile = useIsMobile();

  if (isLoadingCategories || isLoadingHints) {
    return (
      <div className="space-y-6 py-4 flex justify-center">
        <Spinner size="sm" className="text-muted-foreground" />
      </div>
    );
  } else if (isCategoriesError) {
    // We can swallow a hints error, but not a categories error
    return (
      <div className="space-y-6 py-4 flex justify-center">
        <Body className="text-sm text-destructive">Internal Error: Failed to load categories. Please try again later.</Body>
      </div>
    );
  } else {
    return (
      <>
        <div className="space-y-6 py-4">
          <div className="space-y-3">
            <Label htmlFor="event-name" className="text-sm font-medium text-foreground">
              Event Name
            </Label>
            <div className="relative">
              <Input
                id="event-name"
                type={name.type}
                value={name.value}
                onChange={name.onChange}
                className="w-full"
                placeholder="Enter a descriptive name for this event"
              />
            </div>
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
                {categories.map(cat => (
                  <SelectItem key={cat.id} value={cat.name}>
                    {cat.name}
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
            <Button onClick={onClose} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
              Cancel
            </Button>
            <Button
              onClick={createEvent}
              disabled={disableSubmit}
              className={isMobile ? "w-full" : "min-w-[100px]"}
            >
              Create Event
            </Button>
          </div>
        </div>
      </>
    );
  }
}

/**
 * Parent component that handles data fetching and computes initial form values.
 * Uses a key prop to reset the inner component when values should change.
 */
export default function CreateEventModal({ show, onHide }: { show: boolean, onHide: () => void }) {
  const { lineItems } = useLineItems();

  const selectedLineItems = (lineItems || []).filter(lineItem => lineItem.isSelected);
  const selectedLineItemIds = selectedLineItems.map(lineItem => lineItem.id);

  // Fetch prefill suggestion from server when line items are selected
  const { data: prefillSuggestion, isLoading: isLoadingHints, isError: isHintsError } = useEvaluateEventHints(
    selectedLineItemIds,
    selectedLineItemIds.length > 0
  );

  // Show error toast when hints fail to load
  useEffect(() => {
    if (show && isHintsError) {
      showErrorToast("Failed to load event hints. Using default name.");
    }
  }, [show, isHintsError]);

  // Compute initial values based on current state
  const computeInitialValues = () => {
    if (isLoadingHints || selectedLineItems.length === 0) {
      return { name: "", category: "" };
    }
    if (prefillSuggestion) {
      return {
        name: prefillSuggestion.name,
        category: prefillSuggestion.category || "",
      };
    }
    return {
      name: defaultNameCleanup(selectedLineItems[0].description),
      category: "",
    };
  };

  const initialValues = computeInitialValues();

  // Key changes when form should reset:
  // - show: reset when modal opens/closes
  // - isLoadingHints: remount when loading finishes to apply prefill
  // - selectedLineItemIds: reset when selection changes
  const formKey = `${show}-${isLoadingHints}-${selectedLineItemIds.join(',')}`;

  const isMobile = useIsMobile();

  return (
    <ResponsiveDialog open={show} onOpenChange={onHide} className={isMobile ? "" : "w-full !max-w-[42rem]"}>
      <div className="flex flex-col gap-2 pb-4 border-b border-muted">
        <h3 className="text-lg font-semibold text-foreground">New Event Details</h3>
        <p className="text-muted-foreground text-sm">
          Create a financial event from your selected transactions
        </p>
      </div>
      <CreateEventModalContent
        key={formKey}
        initialName={initialValues.name}
        initialCategory={initialValues.category}
        selectedLineItems={selectedLineItems}
        selectedLineItemIds={selectedLineItemIds}
        onClose={onHide}
        isLoadingHints={isLoadingHints}
      />
    </ResponsiveDialog>
  );
}
