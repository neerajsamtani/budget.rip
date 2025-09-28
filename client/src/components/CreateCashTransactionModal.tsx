import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { H3, Body } from "../components/ui/typography";
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
        <DialogContent className="w-full !max-w-[32rem]">
          <DialogHeader className="pb-4 border-b border-[#F5F5F5] -mx-6 px-6">
            <H3 className="text-[#374151]">New Cash Transaction</H3>
            <Body className="text-[#6B7280] mt-2">
              Record a new cash transaction in your budget
            </Body>
          </DialogHeader>
          <div className="space-y-4 -mx-6 px-6">
            <div className="space-y-2">
              <Label htmlFor="event-date" className="text-sm font-medium text-[#374151]">
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
              <Label htmlFor="event-person" className="text-sm font-medium text-[#374151]">
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
              <Label htmlFor="event-description" className="text-sm font-medium text-[#374151]">
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
              <Label htmlFor="event-amount" className="text-sm font-medium text-[#374151]">
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
          <DialogFooter className="pt-4 border-t border-[#F5F5F5] gap-3 -mx-6 px-6">
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