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
import { useCreateSplitwiseExpense, useSplitwiseCurrentUser, useSplitwiseFriends } from "../hooks/useApi";
import { CurrencyFormatter } from "../utils/formatters";
import { parseMoneyToCents } from "../utils/money";
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

type SplitMethod = "equal" | "custom";

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
  const [splitMethod, setSplitMethod] = useState<SplitMethod>("equal");
  const [owedShares, setOwedShares] = useState<Record<number, string>>({});
  const isMobile = useIsMobile();

  const { data: friends = [], isLoading: isLoadingFriends, isError: isFriendsError } = useSplitwiseFriends(show);
  const { data: currentUser, isLoading: isLoadingCurrentUser, isError: isCurrentUserError } = useSplitwiseCurrentUser(show);
  const currentUserId = currentUser?.id;
  const isLoadingSplitwiseData = isLoadingFriends || isLoadingCurrentUser;
  const createExpenseMutation = useCreateSplitwiseExpense();

  useEffect(() => {
    if (show && (isFriendsError || isCurrentUserError)) {
      showErrorToast("Failed to load Splitwise data.");
    }
  }, [show, isFriendsError, isCurrentUserError]);

  const toggleFriend = (friendId: number) => {
    setFriendIds(ids => {
      if (!ids.includes(friendId)) {
        return [...ids, friendId];
      }
      setOwedShares(shares => {
        const nextShares = { ...shares };
        delete nextShares[friendId];
        return nextShares;
      });
      return ids.filter(id => id !== friendId);
    });
  };

  const createExpense = () => {
    const customShares = splitMethod === "custom" && currentUserId !== undefined
      ? Object.fromEntries([currentUserId, ...friendIds].map(userId => [String(userId), Number(owedShares[userId])]))
      : undefined;
    createExpenseMutation.mutate({
      description,
      amount: Number(amount),
      friend_ids: friendIds,
      split_method: splitMethod,
      owed_shares: customShares ?? null,
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

  const parsedAmount = Number(amount);
  const amountCents = parseMoneyToCents(amount);
  const participantIds = currentUserId === undefined ? [] : [currentUserId, ...friendIds];
  const customShareCents = participantIds.map(userId => parseMoneyToCents(owedShares[userId] ?? ""));
  const allocatedCents = customShareCents.reduce<number>((sum, share) => sum + (share ?? 0), 0);
  const remainingCents = (amountCents ?? 0) - allocatedCents;
  const customSplitIsValid = splitMethod === "equal"
    || (participantIds.length > 0 && customShareCents.every(share => share !== null) && remainingCents === 0);
  const disableSubmit = !description.trim()
    || !Number.isFinite(parsedAmount)
    || amountCents === null
    || amountCents <= 0
    || friendIds.length === 0
    || currentUserId === undefined
    || !customSplitIsValid
    || createExpenseMutation.isPending;

  return (
    <ResponsiveDialog
      open={show}
      onOpenChange={onHide}
      className={isMobile ? "" : "max-h-[90vh] w-full !max-w-[34rem] overflow-y-auto overflow-x-hidden"}
    >
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
          <Label>Split method</Label>
          <div className="inline-flex rounded-md border p-1">
            {(["equal", "custom"] as const).map(method => (
              <Button
                key={method}
                type="button"
                size="sm"
                variant={splitMethod === method ? "default" : "ghost"}
                onClick={() => setSplitMethod(method)}
              >
                {method === "equal" ? "Equal" : "Custom"}
              </Button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <Label>Split with</Label>
          <div className="max-h-56 overflow-y-auto rounded-md border bg-white">
            {isLoadingSplitwiseData ? (
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

        {splitMethod === "custom" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Owed shares</Label>
              <Body className="text-sm text-muted-foreground">
                Remaining: {CurrencyFormatter.format(remainingCents / 100)}
              </Body>
            </div>
            <div className="space-y-2">
              {currentUserId !== undefined && (
                <div className="flex items-center gap-3">
                  <Label htmlFor={`splitwise-share-${currentUserId}`} className="flex-1">You</Label>
                  <Input
                    id={`splitwise-share-${currentUserId}`}
                    aria-label="You owed share"
                    type="number"
                    min="0"
                    step="0.01"
                    className="w-28"
                    value={owedShares[currentUserId] ?? ""}
                    onChange={(event) => setOwedShares(shares => ({ ...shares, [currentUserId]: event.target.value }))}
                  />
                </div>
              )}
              {friends.filter(friend => friendIds.includes(friend.id)).map(friend => (
                <div key={friend.id} className="flex items-center gap-3">
                  <Label htmlFor={`splitwise-share-${friend.id}`} className="flex-1">{friend.name}</Label>
                  <Input
                    id={`splitwise-share-${friend.id}`}
                    aria-label={`${friend.name} owed share`}
                    type="number"
                    min="0"
                    step="0.01"
                    className="w-28"
                    value={owedShares[friend.id] ?? ""}
                    onChange={(event) => setOwedShares(shares => ({ ...shares, [friend.id]: event.target.value }))}
                  />
                </div>
              ))}
            </div>
          </div>
        )}
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
