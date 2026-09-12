import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResponsiveDialog, useIsMobile } from "@/components/ui/responsive-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import React, { useState } from 'react';
import { CreateManualTransactionData, useCreateManualTransaction, usePaymentMethods } from '../hooks/useApi';
import { useField } from '../hooks/useField';
import { showErrorToast, showSuccessToast } from '../utils/toast-helpers';

type TransactionDirection = "spent" | "received";

export default function CreateManualTransactionModal({ show, onHide }: { show: boolean, onHide: () => void }) {

  const date = useField<string>("date", "" as string)
  const person = useField<string>("text", "" as string)
  const description = useField<string>("text", "" as string)
  const amount = useField<string>("number", "0")
  const [paymentMethodId, setPaymentMethodId] = useState<string>("")
  const [direction, setDirection] = useState<TransactionDirection>("spent")
  const isMobile = useIsMobile();

  const { data: paymentMethods = [], isLoading: isLoadingPaymentMethods } = usePaymentMethods();
  const createManualTransactionMutation = useCreateManualTransaction();

  const closeAndReset = () => {
    date.setEmpty()
    person.setEmpty()
    description.setEmpty()
    amount.setEmpty()
    setPaymentMethodId("")
    setDirection("spent")
    onHide();
  }

  const createManualTransaction = () => {
    if (!paymentMethodId) {
      showErrorToast(new Error("Please select a payment method"));
      return;
    }

    const amountMagnitude = Number(amount.value.trim());
    if (!amount.value.trim() || !Number.isFinite(amountMagnitude) || amountMagnitude < 0) {
      showErrorToast(new Error("Please enter a valid nonnegative amount"));
      return;
    }

    const newManualTransaction: CreateManualTransactionData = {
      date: date.value,
      person: person.value,
      description: description.value,
      amount: direction === "spent" ? amountMagnitude : -amountMagnitude,
      payment_method_id: paymentMethodId,
    };
    createManualTransactionMutation.mutate(newManualTransaction, {
      onSuccess: () => {
        showSuccessToast("Created Manual Transaction", "Notification");
        closeAndReset();
      },
      onError: (error) => {
        showErrorToast(error);
        closeAndReset();
      }
    });
  }

  return (
    <ResponsiveDialog open={show} onOpenChange={closeAndReset} className={isMobile ? "" : "w-full !max-w-[32rem]"}>
      <div className="flex flex-col gap-2 pb-4 border-b border-muted">
        <h3 className="text-lg font-semibold text-foreground">New Manual Transaction</h3>
        <p className="text-muted-foreground text-sm">
          Record a new transaction manually against any payment method
        </p>
      </div>
      <div className="space-y-4 py-4">
        <div className="space-y-2">
          <Label htmlFor="payment-method" className="text-sm font-medium text-foreground">
            Payment Method
          </Label>
          <Select value={paymentMethodId} onValueChange={setPaymentMethodId}>
            <SelectTrigger id="payment-method" className="w-full">
              <SelectValue placeholder={isLoadingPaymentMethods ? "Loading..." : "Select payment method"} />
            </SelectTrigger>
            <SelectContent className="bg-white border">
              {paymentMethods.map(pm => (
                <SelectItem key={pm.id} value={pm.id}>
                  {pm.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-foreground">Direction</legend>
          <p className="text-sm text-muted-foreground">Choose whether money was spent or received.</p>
          <div className="grid grid-cols-2 gap-3">
            <Label
              htmlFor="direction-spent"
              className="flex min-h-11 cursor-pointer items-center gap-2 rounded-md border border-input px-3 py-2"
            >
              <input
                id="direction-spent"
                name="transaction-direction"
                type="radio"
                value="spent"
                checked={direction === "spent"}
                onChange={() => setDirection("spent")}
              />
              Spent
            </Label>
            <Label
              htmlFor="direction-received"
              className="flex min-h-11 cursor-pointer items-center gap-2 rounded-md border border-input px-3 py-2"
            >
              <input
                id="direction-received"
                name="transaction-direction"
                type="radio"
                value="received"
                checked={direction === "received"}
                onChange={() => setDirection("received")}
              />
              Received
            </Label>
          </div>
        </fieldset>
        <div className="space-y-2">
          <Label htmlFor="event-date" className="text-sm font-medium text-foreground">
            Date
          </Label>
          <Input
            id="event-date"
            value={date.value}
            onChange={date.onChange}
            type={date.type}
            className="w-full"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="event-person" className="text-sm font-medium text-foreground">
            Person
          </Label>
          <Input
            id="event-person"
            value={person.value}
            onChange={person.onChange}
            type={person.type}
            className="w-full"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="event-description" className="text-sm font-medium text-foreground">
            Description
          </Label>
          <Input
            id="event-description"
            value={description.value}
            onChange={description.onChange}
            type={description.type}
            className="w-full"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="event-amount" className="text-sm font-medium text-foreground">
            Amount
          </Label>
          <div className="relative">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-muted-foreground" aria-hidden="true">
              $
            </span>
            <Input
              id="event-amount"
              value={amount.value}
              onChange={amount.onChange}
              type={amount.type}
              inputMode="decimal"
              min="0"
              step="0.01"
              className="w-full pl-8"
              placeholder="0.00"
              aria-describedby="event-amount-help"
            />
          </div>
          <p id="event-amount-help" className="text-sm text-muted-foreground">
            Enter the dollar amount without a sign.
          </p>
        </div>
      </div>
      <div className={`flex pt-4 border-t border-muted gap-3 ${isMobile ? "flex-col" : "justify-end"}`}>
        <Button onClick={closeAndReset} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
          Cancel
        </Button>
        <Button
          onClick={createManualTransaction}
          className={isMobile ? "w-full" : "min-w-[100px]"}
          disabled={createManualTransactionMutation.isPending}
        >
          {createManualTransactionMutation.isPending ? "Creating..." : "Create Transaction"}
        </Button>
      </div>
    </ResponsiveDialog>
  );
}
