import React, { Fragment, useState } from 'react';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { LineItemInterface } from '../contexts/LineItemsContext';
import axiosInstance from '../utils/axiosInstance';
import { EventInterface } from './Event';
import LineItem from './LineItem';
import Notification from './Notification';

export default function EventDetailsModal({ show, event, lineItemsForEvent, onHide }:
  { show: boolean, event: EventInterface, lineItemsForEvent: LineItemInterface[], onHide: () => void }) {

  const [notification, setNotification] = useState(
    {
      heading: "Notification",
      message: "Deleted Event",
      showNotification: false,
    }
  )

  const deleteEvent = () => {
    var VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    axiosInstance.delete(`${VITE_API_ENDPOINT}api/events/${event._id}`)
      .then(response => {
        console.log(response.data);
        setNotification({
          ...notification,
          showNotification: true
        })
        onHide();
      })
      .catch(error => console.log(error));
  }

  return (
    <Fragment>
      <Notification notification={notification} setNotification={setNotification} />
      <Dialog open={show} onOpenChange={onHide}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              {event.name} | {event.category}
            </DialogTitle>
          </DialogHeader>
          <div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Payment Method</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lineItemsForEvent.map(lineItem =>
                  <LineItem key={lineItem._id} lineItem={lineItem} />
                )}
              </TableBody>
            </Table>
            {event.tags && event.tags.length > 0 && (
              <div className="mb-3">
                <strong>Tags: </strong>
                <div className="flex flex-wrap gap-2">
                  {event.tags.map((tag, index) => (
                    <Badge key={index} variant="default">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button onClick={onHide} variant="secondary">Cancel</Button>
            <Button onClick={deleteEvent} variant="destructive">Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Fragment>
  );
}
