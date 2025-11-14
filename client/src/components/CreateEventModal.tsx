import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CATEGORIES } from '@/constants/categories';
import React, { Fragment, useEffect, useState } from 'react';
import { getPrefillFromLineItems } from '.././data/EventHints';
import { Body } from "../components/ui/typography";
import { useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { FormField, useField } from '../hooks/useField';
import { CurrencyFormatter } from '../utils/formatters';
import defaultNameCleanup from '../utils/stringHelpers';
import { showSuccessToast, showErrorToast } from '../utils/toast-helpers';
import { useCreateEvent } from '../hooks/useApi';

interface Tag {
  id: string;
  text: string;
}

export default function CreateEventModal({ show, onHide }: { show: boolean, onHide: () => void }) {

  const lineItems = useLineItems();
  const lineItemsDispatch = useLineItemsDispatch();
  const createEventMutation = useCreateEvent();

  const selectedLineItems = lineItems.filter(lineItem => lineItem.isSelected);
  const selectedLineItemIds = selectedLineItems.map(lineItem => lineItem.id);

  useEffect(() => {
    if (!show && selectedLineItems.length > 0) {
      const prefillSuggestion = getPrefillFromLineItems(selectedLineItems);
      if (prefillSuggestion !== null) {
        name.setCustomValue(prefillSuggestion.name)
        category.setCustomValue(prefillSuggestion.category)
      } else {
        name.setCustomValue(defaultNameCleanup(selectedLineItems[0].description))
      }
    } else if (!show) {
      name.setEmpty()
      category.setEmpty()
    }
    // If we add name or category here, it will cause an infinite render loop
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedLineItems, show])

  const name = useField<string>("text", "" as string)
  const category = useField("select", "All" as string)
  const date = useField<string>("date", "" as string)
  const isDuplicateTransaction = useField<boolean>("checkbox", false)
  const [tags, setTags] = useState<Tag[]>([]);
  const [tagInput, setTagInput] = useState('');

  const disableSubmit = name.value === "" || category.value === "" || category.value === "All"

  const total = React.useMemo(() => {
    return selectedLineItems.reduce((prev, cur) => {
      if (isDuplicateTransaction.value) {
        return prev + cur.amount / 2;
      }
      return prev + cur.amount;
    }, 0);
  }, [selectedLineItems, isDuplicateTransaction]);


  const closeModal = () => {
    name.setEmpty()
    category.setEmpty()
    date.setEmpty()
    setTags([])
    setTagInput('')
    isDuplicateTransaction.setCustomValue(false);
    onHide()
  }

  const handleTagInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      const newTag = {
        id: Math.random().toString(36).substring(2, 9),
        text: tagInput.trim()
      };
      setTags([...tags, newTag]);
      setTagInput('');
    }
  };

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

  return (
    <Fragment>
      <Dialog open={show} onOpenChange={closeModal}>
        <DialogContent className={"w-full !max-w-[42rem]"}>
          <DialogHeader className="pb-4 border-b border-muted -mx-6 px-6">
            <DialogTitle className="text-foreground">New Event Details</DialogTitle>
            <DialogDescription className="text-muted-foreground mt-2">
              Create a financial event from your selected transactions
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 -mx-6 px-6">
            <div className="space-y-3">
              <Label htmlFor="event-name" className="text-sm font-medium text-foreground">
                Event Name
              </Label>
              <Input
                id="event-name"
                type={name.type}
                value={name.value}
                onChange={name.onChange}
                className="w-full !min-w-[350px]"
                placeholder="Enter a descriptive name for this event"
              />
            </div>

            <div className="space-y-3">
              {/* TODO: Is it possible to replace this with a CategoryFilter component? */}
              <Label htmlFor="event-category" className="text-sm font-medium text-foreground">
                Category
              </Label>
              <Select value={category.value} onValueChange={(value) => category.setCustomValue(value)}>
                <SelectTrigger className="w-full !min-w-[350px]">
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

            <div className="space-y-3">
              {/* TODO: Create a separate component for adding / removing tags */}
              <Label htmlFor="event-tags" className="text-sm font-medium text-foreground">
                Tags
              </Label>
              <div className="space-y-3">
                {tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {tags.map(tag => (
                      <Badge
                        key={tag.id}
                        className="bg-primary text-white hover:bg-primary-dark flex items-center gap-1 px-3 py-1">
                        {tag.text}
                        <span
                          onClick={() => removeTag(tag.id)}
                          className="ml-1 cursor-pointer hover:text-red-300 font-bold"
                        >
                          ×
                        </span>
                      </Badge>
                    ))}
                  </div>
                )}
                <Input
                  id="event-tags"
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleTagInputKeyDown}
                  placeholder="Type a tag and press Enter to add"
                  className="w-full !min-w-[350px]"
                />
              </div>
            </div>

            <div className="space-y-3">
              <Label htmlFor="override-date-input" className="text-sm font-medium text-foreground">
                Override Date (optional)
              </Label>
              <Input
                id="override-date-input"
                type={date.type}
                value={date.value}
                onChange={date.onChange}
                className="w-full !min-w-[350px]"
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

          <DialogFooter className="pt-4 border-t border-muted -mx-6 px-6">
            <div className="flex items-center justify-between w-full">
              <div className="bg-muted px-4 py-2 rounded-lg">
                <Body className="text-sm font-medium text-foreground">
                  Total: <span className="text-primary font-semibold">{CurrencyFormatter.format(total)}</span>
                </Body>
              </div>
              <div className="flex space-x-3">
                <Button onClick={closeModal} variant="secondary" className="min-w-[100px]">
                  Cancel
                </Button>
                <Button
                  onClick={() => createEvent(name, category)}
                  disabled={disableSubmit}
                  className="min-w-[100px]"
                >
                  Create Event
                </Button>
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Fragment >
  );
}
