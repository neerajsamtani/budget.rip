import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ResponsiveDialog, ResponsiveDialogFooter, ResponsiveDialogHeader, useIsMobile } from "@/components/ui/responsive-dialog";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import React from 'react';
import { Body, H3 } from "../components/ui/typography";
import { LineItemInterface } from '../contexts/LineItemsContext';
import { showSuccessToast, showErrorToast } from '../utils/toast-helpers';
import { EventInterface } from './Event';
import LineItem, { LineItemCard } from './LineItem';
import { useDeleteEvent } from '../hooks/useApi';

export default function EventDetailsModal({ show, event, lineItemsForEvent, onHide }:
  { show: boolean, event: EventInterface, lineItemsForEvent: LineItemInterface[], onHide: () => void }) {

  const deleteEventMutation = useDeleteEvent();
  const isMobile = useIsMobile();

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
    <ResponsiveDialog open={show} onOpenChange={onHide} className={isMobile ? "" : "w-full !max-w-[56rem]"}>
      <ResponsiveDialogHeader className="pb-4 border-b border-muted">
        <H3 className="text-foreground">{event.name}</H3>
        <Body className="text-muted-foreground mt-2">
          Category: <span className="font-medium text-primary">{event.category}</span>
        </Body>
      </ResponsiveDialogHeader>
      <div className="space-y-6">
        {isMobile ? (
          <div className="rounded-xl bg-muted/50 border overflow-hidden">
            {lineItemsForEvent.map(lineItem => (
              <LineItemCard
                key={lineItem.id}
                lineItem={lineItem}
                showCheckBox={false}
                isChecked={false}
                handleToggle={() => {}}
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
                {lineItemsForEvent.map(lineItem =>
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
      <ResponsiveDialogFooter className="pt-4 border-t border-muted gap-3">
        <Button onClick={onHide} variant="secondary" className="min-w-[100px]">
          Close
        </Button>
        <Button onClick={deleteEvent} variant="destructive" className="min-w-[100px]">
          Delete Event
        </Button>
      </ResponsiveDialogFooter>
    </ResponsiveDialog>
  );
}
