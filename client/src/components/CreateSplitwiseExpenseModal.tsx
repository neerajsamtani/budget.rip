import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResponsiveDialog, ResponsiveDialogDescription, ResponsiveDialogTitle, useIsMobile } from "@/components/ui/responsive-dialog";
import { Spinner } from "@/components/ui/spinner";
import { Body } from "@/components/ui/typography";
import { DateTime } from "luxon";
import React, { useEffect, useMemo, useState } from "react";
import { LineItemInterface } from "../contexts/LineItemsContext";
import { useCreateSplitwiseExpense, useSplitwiseFriends } from "../hooks/useApi";
import { CurrencyFormatter } from "../utils/formatters";
import defaultNameCleanup from "../utils/stringHelpers";
import { showErrorToast, showSuccessToast } from "../utils/toast-helpers";

interface CreateSplitwiseExpenseModalProps {
  show: boolean;
  onHide: () => void;
  selectedLineItems: LineItemInterface[];
}

interface CreateSplitwiseExpenseFormProps {
  show: boolean;
  onHide: () => void;
  defaultDescription: string;
  defaultAmount: string;
  defaultDate: string;
  selectedTotal: number;
}

function CreateSplitwiseExpenseForm({
  show,
  onHide,
  defaultDescription,
  defaultAmount,
  defaultDate,
  selectedTotal,
}: CreateSplitwiseExpenseFormProps) {
  const [description, setDescription] = useState(defaultDescription);
  const [amount, setAmount] = useState(defaultAmount);
  const [date, setDate] = useState(defaultDate);
  const [friendIds, setFriendIds] = useState<number[]>([]);
  const isMobile = useIsMobile();

  const { data: friends = [], isLoading: isLoadingFriends, isError: isFriendsError } = useSplitwiseFriends(show);
  const createExpenseMutation = useCreateSplitwiseExpense();

  useEffect(() => {
    if (show && isFriendsError) {
      showErrorToast("Failed to load Splitwise friends.");
    }
  }, [show, isFriendsError]);

  const toggleFriend = (friendId: number) => {
    setFriendIds(ids => ids.includes(friendId) ? ids.filter(id => id !== friendId) : [...ids, friendId]);
  };

  const createExpense = () => {
    createExpenseMutation.mutate({
      description,
      amount: Number(amount),
      friend_ids: friendIds,
      date: date || undefined,
      currency_code: "USD",
    }, {
      onSuccess: () => {
        showSuccessToast("Created Splitwise Expense", "Notification");
        onHide();
      },
      onError: (error) => {
        showErrorToast(error);
      }
    });
  };

  const disableSubmit = !description.trim() || Number(amount) <= 0 || friendIds.length === 0 || createExpenseMutation.isPending;

  return (
    <ResponsiveDialog open={show} onOpenChange={onHide} className={isMobile ? "" : "w-full !max-w-[34rem]"}>
      <div className="flex flex-col gap-2 pb-4 border-b border-muted">
        <ResponsiveDialogTitle className="text-lg font-semibold text-foreground">New Splitwise Expense</ResponsiveDialogTitle>
        <ResponsiveDialogDescription className="text-muted-foreground text-sm">
          Split the selected review total with friends in Splitwise
        </ResponsiveDialogDescription>
      </div>

      <div className="space-y-4 py-4">
        <div className="rounded-lg bg-muted px-4 py-3">
          <Body className="text-sm font-medium text-foreground">
            Selected total: {CurrencyFormatter.format(Math.abs(selectedTotal))}
          </Body>
        </div>

        <div className="space-y-2">
          <Label htmlFor="splitwise-description">Description</Label>
          <Input
            id="splitwise-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="splitwise-amount">Amount</Label>
            <Input
              id="splitwise-amount"
              type="number"
              min="0"
              step="0.01"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="splitwise-date">Date</Label>
            <Input
              id="splitwise-date"
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
            />
          </div>
        </div>

        <div className="space-y-3">
          <Label>Split with</Label>
          <div className="max-h-56 overflow-y-auto rounded-md border bg-white">
            {isLoadingFriends ? (
              <div className="flex justify-center py-6">
                <Spinner size="sm" className="text-muted-foreground" />
              </div>
            ) : friends.length > 0 ? (
              friends.map(friend => (
                <label key={friend.id} className="flex items-center gap-3 border-b last:border-b-0 px-3 py-2 cursor-pointer">
                  <Checkbox
                    checked={friendIds.includes(friend.id)}
                    onCheckedChange={() => toggleFriend(friend.id)}
                  />
                  <span className="text-sm text-foreground">{friend.name}</span>
                </label>
              ))
            ) : (
              <div className="px-3 py-6 text-center text-sm text-muted-foreground">
                No Splitwise friends found
              </div>
            )}
          </div>
        </div>
      </div>

      <div className={`flex pt-4 border-t border-muted gap-3 ${isMobile ? "flex-col" : "justify-end"}`}>
        <Button onClick={onHide} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
          Cancel
        </Button>
        <Button onClick={createExpense} disabled={disableSubmit} className={isMobile ? "w-full" : "min-w-[100px]"}>
          {createExpenseMutation.isPending ? "Creating..." : "Create Expense"}
        </Button>
      </div>
    </ResponsiveDialog>
  );
}

export default function CreateSplitwiseExpenseModal({ show, onHide, selectedLineItems }: CreateSplitwiseExpenseModalProps) {
  const selectedTotal = useMemo(
    () => selectedLineItems.reduce((sum, lineItem) => sum + lineItem.amount, 0),
    [selectedLineItems]
  );
  const defaultDescription = selectedLineItems.length === 1
    ? defaultNameCleanup(selectedLineItems[0].description)
    : "Shared expense";
  const defaultDate = selectedLineItems.length > 0
    ? DateTime.fromSeconds(Math.min(...selectedLineItems.map(lineItem => lineItem.date)), { zone: 'utc' }).toISODate() || ""
    : "";
  const defaultAmount = Math.abs(selectedTotal).toFixed(2);
  const formKey = `${show}-${selectedLineItems.map(lineItem => lineItem.id).join(",")}`;

  return (
    <CreateSplitwiseExpenseForm
      key={formKey}
      show={show}
      onHide={onHide}
      defaultDescription={defaultDescription}
      defaultAmount={defaultAmount}
      defaultDate={defaultDate}
      selectedTotal={selectedTotal}
    />
  );
}
