import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import React, { Fragment } from 'react';
import { Body, H3 } from "../components/ui/typography";
import { useField } from '../hooks/useField';
import axiosInstance from '../utils/axiosInstance';
import { showErrorToast, showSuccessToast } from '../utils/toast-helpers';
import { MODAL_WIDTHS } from '@/constants/ui';

export default function CreateCashTransactionModal({ show, onHide }: { show: boolean, onHide: () => void }) {

  const date = useField<string>("date", "" as string)
  const person = useField<string>("text", "" as string)
  const description = useField<string>("text", "" as string)
  const amount = useField<number>("number", 0 as number)

  const createCashTransaction = () => {
    const newCashTransaction = {
      "date": date.value,
      "person": person.value,
      "description": description.value,
      "amount": amount.value
    }
    axiosInstance.post(`api/cash_transaction`, newCashTransaction)
      .then(() => {
        date.setEmpty()
        person.setEmpty()
        description.setEmpty()
        amount.setEmpty()
        showSuccessToast("Created Cash Transaction", "Notification");
        // TODO: Uncheck all checkboxes
        onHide();
      })
      .catch(showErrorToast);
  }

  return (
    <Fragment>
      <Dialog open={show} onOpenChange={onHide}>
        <DialogContent className={`w-full !max-w-[${MODAL_WIDTHS.SMALL}]`}>
          <DialogHeader className="pb-4 border-b border-muted -mx-6 px-6">
            <H3 className="text-foreground">New Cash Transaction</H3>
            <Body className="text-muted-foreground mt-2">
              Record a new cash transaction in your budget
            </Body>
          </DialogHeader>
          <div className="space-y-4 -mx-6 px-6">
            <div className="space-y-2">
              <Label htmlFor="event-date" className="text-sm font-medium text-foreground">
                Date
              </Label>
              <Input
                id="event-date"
                value={date.value}
                onChange={date.onChange}
                type={date.type}
                className="w-full !min-w-[300px]"
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
                className="w-full !min-w-[300px]"
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
                className="w-full !min-w-[300px]"
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
                className="w-full !min-w-[300px]"
                placeholder="0.00"
              />
            </div>
          </div>
          <DialogFooter className="pt-4 border-t border-muted gap-3 -mx-6 px-6">
            <Button onClick={onHide} variant="secondary" className="min-w-[100px]">
              Cancel
            </Button>
            <Button onClick={createCashTransaction} className="min-w-[100px]">
              Create Transaction
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Fragment>
  );
}