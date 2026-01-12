import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ResponsiveDialog, ResponsiveDialogDescription, ResponsiveDialogTitle, useIsMobile } from "@/components/ui/responsive-dialog";
import { Textarea } from "@/components/ui/textarea";
import React, { useEffect, useState } from 'react';
import { LineItemInterface, useLineItemsDispatch } from '../contexts/LineItemsContext';
import { useDeleteManualTransaction, useUpdateLineItem } from '../hooks/useApi';
import { CurrencyFormatter, DateFormatter } from '../utils/formatters';
import { showErrorToast, showSuccessToast } from '../utils/toast-helpers';
import { StatusBadge } from "./ui/status-badge";

interface LineItemDetailsModalProps {
  show: boolean;
  lineItem: LineItemInterface;
  onHide: () => void;
}

export default function LineItemDetailsModal({ show, lineItem, onHide }: LineItemDetailsModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [notes, setNotes] = useState(lineItem.notes || '');

  const updateLineItemMutation = useUpdateLineItem();
  const deleteManualTransactionMutation = useDeleteManualTransaction();
  const lineItemsDispatch = useLineItemsDispatch();
  const isMobile = useIsMobile();

  useEffect(() => {
    if (show) {
      setNotes(lineItem.notes || '');
      setIsEditing(false);
    }
  }, [show, lineItem]);

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setIsEditing(false);
      onHide();
    }
  };

  const handleSaveNotes = () => {
    updateLineItemMutation.mutate(
      { lineItemId: lineItem.id, notes: notes || undefined },
      {
        onSuccess: () => {
          showSuccessToast(lineItem.description, "Updated Notes");
          setIsEditing(false);
        },
        onError: (error) => {
          showErrorToast(error);
        },
      }
    );
  };

  const handleDelete = () => {
    if (!lineItem.transaction_id) {
      showErrorToast(new Error("Cannot delete: missing transaction ID"));
      return;
    }

    deleteManualTransactionMutation.mutate(lineItem.transaction_id, {
      onSuccess: () => {
        lineItemsDispatch({
          type: 'remove_line_items',
          lineItemIds: [lineItem.id],
        });
        showSuccessToast(lineItem.description, "Deleted Transaction");
        onHide();
      },
      onError: (error) => {
        showErrorToast(error);
      },
    });
  };

  const readableDate = DateFormatter.format(lineItem.date * 1000);
  const amountStatus: 'success' | 'warning' = lineItem.amount < 0 ? 'success' : 'warning';

  return (
    <ResponsiveDialog open={show} onOpenChange={handleOpenChange}>
      {isEditing ? (
        <>
          <div className="flex flex-col gap-2 pb-4 border-b border-muted">
            <ResponsiveDialogTitle className="text-foreground">Edit Notes</ResponsiveDialogTitle>
            <ResponsiveDialogDescription className="text-muted-foreground">
              {lineItem.description}
            </ResponsiveDialogDescription>
          </div>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="line-item-notes">Notes</Label>
              <Textarea
                id="line-item-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add notes about this transaction..."
                rows={4}
              />
            </div>
          </div>
          <div className={`flex pt-4 border-t border-muted gap-3 ${isMobile ? "flex-col" : "justify-end"}`}>
            <Button
              onClick={() => setIsEditing(false)}
              variant="secondary"
              className={isMobile ? "w-full" : "min-w-[100px]"}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveNotes}
              disabled={updateLineItemMutation.isPending}
              className={isMobile ? "w-full" : "min-w-[100px]"}
            >
              {updateLineItemMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </div>
        </>
      ) : (
        <>
          <div className="flex flex-col gap-2 pb-4 border-b border-muted">
            <ResponsiveDialogTitle className="text-foreground">Transaction Details</ResponsiveDialogTitle>
            <ResponsiveDialogDescription className="text-muted-foreground">
              {lineItem.description}
            </ResponsiveDialogDescription>
          </div>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground text-sm">Date</Label>
                <p className="text-foreground">{readableDate}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-sm">Amount</Label>
                <div className="mt-1">
                  <StatusBadge status={amountStatus}>
                    {CurrencyFormatter.format(Math.abs(lineItem.amount))}
                  </StatusBadge>
                </div>
              </div>
              <div>
                <Label className="text-muted-foreground text-sm">Payment Method</Label>
                <p className="text-foreground">{lineItem.payment_method}</p>
              </div>
              <div>
                <Label className="text-muted-foreground text-sm">Responsible Party</Label>
                <p className="text-foreground">{lineItem.responsible_party || '-'}</p>
              </div>
              {lineItem.bank_account && (
                <div className="col-span-2">
                  <Label className="text-muted-foreground text-sm">Account Details</Label>
                  <p className="text-foreground">
                    {lineItem.bank_account.institution_name} - {lineItem.bank_account.display_name} (****{lineItem.bank_account.last4})
                  </p>
                </div>
              )}
            </div>
            {lineItem.notes && (
              <div>
                <Label className="text-muted-foreground text-sm">Notes</Label>
                <p className="text-foreground whitespace-pre-wrap">{lineItem.notes}</p>
              </div>
            )}
          </div>
          <div className={`flex pt-4 border-t border-muted gap-3 ${isMobile ? "flex-col" : "justify-end"}`}>
            <Button
              onClick={() => setIsEditing(true)}
              variant="secondary"
              className={isMobile ? "w-full" : "min-w-[100px]"}
            >
              {lineItem.notes ? "Edit Notes" : "Add Notes"}
            </Button>
            {lineItem.is_manual && (
              <Button
                onClick={handleDelete}
                variant="destructive"
                disabled={deleteManualTransactionMutation.isPending}
                className={isMobile ? "w-full" : "min-w-[100px]"}
              >
                {deleteManualTransactionMutation.isPending ? "Deleting..." : "Delete"}
              </Button>
            )}
          </div>
        </>
      )}
    </ResponsiveDialog>
  );
}
