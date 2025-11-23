import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResponsiveDialog, useIsMobile } from "@/components/ui/responsive-dialog";
import React from 'react';
import { useField } from '../hooks/useField';
import { showSuccessToast, showErrorToast } from '../utils/toast-helpers';
import { useCreateCashTransaction } from '../hooks/useApi';

export default function CreateCashTransactionModal({ show, onHide }: { show: boolean, onHide: () => void }) {

  const date = useField<string>("date", "" as string)
  const person = useField<string>("text", "" as string)
  const description = useField<string>("text", "" as string)
  const amount = useField<number>("number", 0 as number)
  const isMobile = useIsMobile();

  const createCashTransactionMutation = useCreateCashTransaction();

  const createCashTransaction = () => {
    const newCashTransaction = {
      "date": date.value,
      "person": person.value,
      "description": description.value,
      "amount": amount.value
    }
    createCashTransactionMutation.mutate(newCashTransaction as any, {
      onSuccess: () => {
        date.setEmpty()
        person.setEmpty()
        description.setEmpty()
        amount.setEmpty()
        showSuccessToast("Created Cash Transaction", "Notification");
        onHide();
      },
      onError: (error) => {
        showErrorToast(error);
      }
    });
  }

  return (
    <ResponsiveDialog open={show} onOpenChange={onHide} className={isMobile ? "" : "w-full !max-w-[32rem]"}>
      <div className="flex flex-col gap-2 pb-4 border-b border-muted">
        <h3 className="text-lg font-semibold text-foreground">New Cash Transaction</h3>
        <p className="text-muted-foreground text-sm">
          Record a new cash transaction in your budget
        </p>
      </div>
      <div className="space-y-4 py-4">
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
          <Input
            id="event-amount"
            value={amount.value}
            onChange={amount.onChange}
            type={amount.type}
            className="w-full"
            placeholder="0.00"
          />
        </div>
      </div>
      <div className={`flex pt-4 border-t border-muted gap-3 ${isMobile ? "flex-col" : "justify-end"}`}>
        <Button onClick={onHide} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
          Cancel
        </Button>
        <Button onClick={createCashTransaction} className={isMobile ? "w-full" : "min-w-[100px]"}>
          Create Transaction
        </Button>
      </div>
    </ResponsiveDialog>
  );
}