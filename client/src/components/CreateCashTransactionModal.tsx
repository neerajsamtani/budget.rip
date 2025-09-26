import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import React, { Fragment } from 'react';
import { toast } from 'sonner';
import { useField } from '../hooks/useField';
import axiosInstance from '../utils/axiosInstance';

export default function CreateCashTransactionModal({ show, onHide }: { show: boolean, onHide: () => void }) {

  const date = useField<string>("date", "" as string)
  const person = useField<string>("text", "" as string)
  const description = useField<string>("text", "" as string)
  const amount = useField<number>("number", 0 as number)

  const createCashTransaction = () => {
    const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    const newCashTransaction = {
      "date": date.value,
      "person": person.value,
      "description": description.value,
      "amount": amount.value
    }
    axiosInstance.post(`${VITE_API_ENDPOINT}api/cash_transaction`, newCashTransaction)
      .then(() => {
        date.setEmpty()
        person.setEmpty()
        description.setEmpty()
        amount.setEmpty()
        toast.success("Notification", {
          description: "Created Cash Transaction",
          duration: 3500,
        });
        // TODO: Uncheck all checkboxes
        onHide();
      })
      .catch(error => console.log(error));
  }

  return (
    <Fragment>
      <Dialog open={show} onOpenChange={onHide}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              New Cash Transaction
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              {/* TODO: DATE PICKER */}
              <Label htmlFor="event-date">Date:</Label>
              <Input id="event-date" value={date.value} onChange={date.onChange} type={date.type} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="event-person">Person:</Label>
              <Input id="event-person" value={person.value} onChange={person.onChange} type={person.type} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="event-description">Description:</Label>
              <Input id="event-description" value={description.value} onChange={description.onChange} type={description.type} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="event-amount">Amount:</Label>
              <Input id="event-amount" value={amount.value} onChange={amount.onChange} type={amount.type} />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={onHide} variant="secondary">Cancel</Button>
            <Button onClick={createCashTransaction}>Submit</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Fragment>
  );
}