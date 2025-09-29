import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader } from "@/components/ui/dialog";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import React, { Fragment } from 'react';
import { toast } from 'sonner';
import { Body, H3 } from "../components/ui/typography";
import { LineItemInterface } from '../contexts/LineItemsContext';
import axiosInstance from '../utils/axiosInstance';
import { EventInterface } from './Event';
import LineItem from './LineItem';

export default function EventDetailsModal({ show, event, lineItemsForEvent, onHide }:
  { show: boolean, event: EventInterface, lineItemsForEvent: LineItemInterface[], onHide: () => void }) {


  const deleteEvent = () => {
    const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    axiosInstance.delete(`${VITE_API_ENDPOINT}api/events/${event._id}`)
      .then(() => {
        toast.success("Deleted Event", {
          description: event.name,
          duration: 3500,
        });
        onHide();
      })
      .catch(error => toast.error("Error", {
        description: error.message,
        duration: 3500,
      }));
  }

  return (
    <Fragment>
      <Dialog open={show} onOpenChange={onHide}>
        <DialogContent className="w-full !max-w-[56rem]">
          <DialogHeader className="pb-4 border-b border-muted -mx-6 px-6">
            <H3 className="text-foreground">{event.name}</H3>
            <Body className="text-muted-foreground mt-2">
              Category: <span className="font-medium text-primary">{event.category}</span>
            </Body>
          </DialogHeader>
          <div className="space-y-6 -mx-6 px-6">
            <div className="overflow-x-auto">
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
            </div>
            {event.tags && event.tags.length > 0 && (
              <div className="space-y-3">
                <Body className="font-medium text-foreground">Tags:</Body>
                <div className="flex flex-wrap gap-2">
                  {event.tags.map((tag, index) => (
                    <Badge key={index} className="bg-primary text-white px-3 py-1">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
          <DialogFooter className="pt-4 border-t border-muted gap-3 -mx-6 px-6">
            <Button onClick={onHide} variant="secondary" className="min-w-[100px]">
              Close
            </Button>
            <Button onClick={deleteEvent} variant="destructive" className="min-w-[100px]">
              Delete Event
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Fragment>
  );
}
