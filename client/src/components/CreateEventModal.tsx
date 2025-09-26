import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import React, { Fragment, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { getPrefillFromLineItems } from '.././data/EventHints';
import { useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { FormField, useField } from '../hooks/useField';
import axiosInstance from '../utils/axiosInstance';
import { CurrencyFormatter } from '../utils/formatters';
import defaultNameCleanup from '../utils/stringHelpers';

interface Tag {
  id: string;
  text: string;
}

export default function CreateEventModal({ show, onHide }: { show: boolean, onHide: () => void }) {

  const lineItems = useLineItems();
  const lineItemsDispatch = useLineItemsDispatch();

  const selectedLineItems = lineItems.filter(lineItem => lineItem.isSelected);
  const selectedLineItemIds = lineItems.filter(lineItem => lineItem.isSelected).map(lineItem => lineItem.id);
  // TODO: Make hints more robust with categories
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
    const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    const newEvent = {
      "name": name.value,
      "category": category.value,
      "date": date.value,
      "line_items": selectedLineItemIds,
      "is_duplicate_transaction": isDuplicateTransaction.value,
      "tags": tags.map(tag => tag.text)
    }
    console.log(newEvent);
    axiosInstance.post(`${VITE_API_ENDPOINT}api/events`, newEvent)
      .then(response => {
        console.log(response.data);
      })
      .then(() => {
        closeModal()
        lineItemsDispatch({
          type: 'remove_line_items',
          lineItemIds: selectedLineItemIds
        })
        toast.success("Notification", {
          description: "Created Event",
          duration: 3500,
        });
        // TODO: Uncheck all checkboxes
      })
      .catch(error => console.log(error));
  }

  return (
    <Fragment>
      <Dialog open={show} onOpenChange={closeModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              New Event Details
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Name:</Label>
              <Input type={name.type} value={name.value} onChange={name.onChange} />
            </div>
            {/* TODO: Can I use a CategoryFilter here? */}
            <div className="space-y-2">
              <Label>Category:</Label>
              <Select value={category.value} onValueChange={(value) => category.setCustomValue(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All">All</SelectItem>
                  <SelectItem value="Alcohol">Alcohol</SelectItem>
                  <SelectItem value="Dining">Dining</SelectItem>
                  <SelectItem value="Entertainment">Entertainment</SelectItem>
                  <SelectItem value="Forma">Forma</SelectItem>
                  <SelectItem value="Groceries">Groceries</SelectItem>
                  <SelectItem value="Hobbies">Hobbies</SelectItem>
                  <SelectItem value="Income">Income</SelectItem>
                  <SelectItem value="Investment">Investment</SelectItem>
                  <SelectItem value="Medical">Medical</SelectItem>
                  <SelectItem value="Rent">Rent</SelectItem>
                  <SelectItem value="Shopping">Shopping</SelectItem>
                  <SelectItem value="Subscription">Subscription</SelectItem>
                  <SelectItem value="Transfer">Transfer</SelectItem>
                  <SelectItem value="Transit">Transit</SelectItem>
                  <SelectItem value="Travel">Travel</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Tags:</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {tags.map(tag => (
                  <Badge
                    key={tag.id}
                    variant="default"
                    className="flex items-center gap-1"
                  >
                    {tag.text}
                    <span
                      onClick={() => removeTag(tag.id)}
                      className="ml-1 cursor-pointer hover:text-red-500"
                    >
                      ×
                    </span>
                  </Badge>
                ))}
              </div>
              <Input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagInputKeyDown}
                placeholder="Type a tag and press Enter"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="override-date-input">Override Date:</Label>
              <Input id="override-date-input" type={date.type} value={date.value} onChange={date.onChange} />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="duplicate-transaction"
                checked={isDuplicateTransaction.value}
                onCheckedChange={() => isDuplicateTransaction.setCustomValue(!isDuplicateTransaction.value)}
              />
              <Label htmlFor="duplicate-transaction">Duplicate Transaction</Label>
            </div>
          </div>
          <DialogFooter>
            <div className="flex items-center justify-between w-full">
              <Badge variant="secondary">Total: {CurrencyFormatter.format(total)}</Badge>
              <div className="flex space-x-2">
                <Button onClick={closeModal} variant="secondary">Cancel</Button>
                <Button onClick={() => createEvent(name, category)} disabled={disableSubmit}>Submit</Button>
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Fragment >
  );
}
