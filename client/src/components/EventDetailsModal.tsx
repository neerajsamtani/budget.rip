import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ResponsiveDialog, ResponsiveDialogTitle, ResponsiveDialogDescription, useIsMobile } from "@/components/ui/responsive-dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import React from 'react';
import { Body } from "../components/ui/typography";
import { LineItemInterface } from '../contexts/LineItemsContext';
import { useDeleteEvent } from '../hooks/useApi';
import { showErrorToast, showSuccessToast } from '../utils/toast-helpers';
import { EventInterface } from './Event';
import LineItem, { LineItemCard } from './LineItem';
import { Spinner } from "./ui/spinner";

export default function EventDetailsModal({ show, event, lineItemsForEvent, isLoadingLineItemsForEvent, onHide }:
  { show: boolean, event: EventInterface, lineItemsForEvent: LineItemInterface[], isLoadingLineItemsForEvent: boolean, onHide: () => void }) {

  const deleteEventMutation = useDeleteEvent();
  const isMobile = useIsMobile();

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      onHide();
    }
  };

  const deleteEvent = () => {
    deleteEventMutation.mutate(event.id, {
      onSuccess: () => {
        showSuccessToast(event.name, "Deleted Event");
        onHide();
      },
      onError: (error) => {
        showErrorToast(error);
      }
    });
  }

  return (
    <ResponsiveDialog open={show} onOpenChange={handleOpenChange} className={isMobile ? "" : "w-full !max-w-[56rem]"}>
      <div className="flex flex-col gap-2 pb-4 border-b border-muted">
        <ResponsiveDialogTitle className="text-foreground">{event.name}</ResponsiveDialogTitle>
        <ResponsiveDialogDescription className="text-muted-foreground">
          Category: <span className="font-medium text-primary">{event.category}</span>
        </ResponsiveDialogDescription>
      </div>
      <div className="space-y-6 py-4 overflow-y-auto max-h-[60vh]">
        {isMobile ? (
          <div className="rounded-xl bg-muted/50 border overflow-hidden">
            {isLoadingLineItemsForEvent ? (<div className="flex justify-center items-center p-4">
              <Spinner size="sm" />
            </div>) : lineItemsForEvent.map(lineItem => (
              <LineItemCard
                key={lineItem.id}
                lineItem={lineItem}
                showCheckBox={false}
                isChecked={false}
                handleToggle={() => { }}
                amountStatus={lineItem.amount < 0 ? 'success' : 'warning'}
              />
            ))}
          </div>
        ) : (
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
                {isLoadingLineItemsForEvent ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-8 text-center">
                      <div className="flex justify-center items-center w-full">
                        <Spinner size="sm" />
                      </div>
                    </TableCell>
                  </TableRow>
                ) : lineItemsForEvent.map(lineItem =>
                  <LineItem key={lineItem.id} lineItem={lineItem} />
                )}
              </TableBody>
            </Table>
          </div>
        )}
        {event.tags && event.tags.length > 0 && (
          <div className="flex items-center gap-3">
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
      <div className={`flex pt-4 border-t border-muted gap-3 ${isMobile ? "flex-col" : "justify-end"}`}>
        <Button onClick={onHide} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
          Close
        </Button>
        <Button onClick={deleteEvent} variant="destructive" className={isMobile ? "w-full" : "min-w-[100px]"}>
          Delete Event
        </Button>
      </div>
    </ResponsiveDialog>
  );
}
