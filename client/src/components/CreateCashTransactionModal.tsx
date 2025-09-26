import React, { Fragment, useState } from 'react';
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useField } from '../hooks/useField';
import axiosInstance from '../utils/axiosInstance';
import Notification from './Notification';

export default function CreateCashTransactionModal({ show, onHide }: { show: boolean, onHide: () => void }) {
  const [notification, setNotification] = useState(
    {
      heading: "Notification",
      message: "Created Cash Transaction",
      showNotification: false,
    }
  )

  const date = useField<string>("date", "" as string)
  const person = useField<string>("text", "" as string)
  const description = useField<string>("text", "" as string)
  const amount = useField<number>("number", 0 as number)

  const createCashTransaction = () => {
    var VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    var newCashTransaction = {
      "date": date.value,
      "person": person.value,
      "description": description.value,
      "amount": amount.value
    }
    console.log(newCashTransaction);
    axiosInstance.post(`${VITE_API_ENDPOINT}api/cash_transaction`, newCashTransaction)
      .then(response => {
        console.log(response.data);
      })
      .then(() => {
        date.setEmpty()
        person.setEmpty()
        description.setEmpty()
        amount.setEmpty()
        setNotification({
          ...notification,
          showNotification: true
        })
        // TODO: Uncheck all checkboxes
        onHide();
      })
      .catch(error => console.log(error));
  }

  return (
    <Fragment>
      <Notification notification={notification} setNotification={setNotification} />
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