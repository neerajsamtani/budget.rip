import { EventInterface } from '@/components/Event';
import EventDetailsModal from '@/components/EventDetailsModal';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { useEventLineItems } from '@/hooks/useApi';
import { CurrencyFormatter } from '@/utils/formatters';
import { DateTime } from 'luxon';
import React, { useMemo, useState } from 'react';
import { formatMonthYear } from './chart-utils';

interface Props {
  open: boolean;
  // 'all' means all categories (column total was clicked)
  category: string;
  // 'all' means all months (row total was clicked)
  date: string;
  events: EventInterface[];
  onClose: () => void;
}

export default function SpendingDrillDown({ open, category, date, events, onClose }: Props) {
  const [selectedEvent, setSelectedEvent] = useState<EventInterface | null>(null);
  const { data: lineItemsForSelectedEvent = [], isLoading: isLoadingLineItems } = useEventLineItems(
    selectedEvent?.id ?? ''
  );

  const isAllDates = date === 'all';
  const isAllCategories = category === 'all';

  const matched = useMemo(() => {
    if (!open || !date || !category) return [];

    if (isAllDates && isAllCategories) {
      return [...events].sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
    }

    if (isAllDates) {
      return events
        .filter(e => e.category === category)
        .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
    }

    const [month, year] = date.split('-').map(Number);

    if (isAllCategories) {
      return events
        .filter(e => {
          const dt = DateTime.fromSeconds(e.date, { zone: 'utc' });
          return dt.month === month && dt.year === year;
        })
        .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
    }

    return events
      .filter(e => {
        const dt = DateTime.fromSeconds(e.date, { zone: 'utc' });
        return e.category === category && dt.month === month && dt.year === year;
      })
      .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
  }, [open, date, category, events, isAllDates, isAllCategories]);

  const formattedDate = date && !isAllDates ? formatMonthYear(date) : '';
  const title = isAllDates && isAllCategories
    ? 'Top Events'
    : isAllCategories
    ? formattedDate
    : category;
  const description = isAllDates && isAllCategories
    ? 'Highest expenses'
    : isAllDates
    ? 'All months'
    : isAllCategories
    ? 'All categories'
    : formattedDate;

  return (
    <>
      <Sheet open={open} onOpenChange={o => { if (!o) onClose(); }}>
        <SheetContent className="overflow-hidden">
          <SheetHeader>
            <SheetTitle>{title}</SheetTitle>
            <SheetDescription>{description}</SheetDescription>
          </SheetHeader>
          <div className="flex-1 min-h-0 overflow-y-auto mt-4">
            {matched.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No events found.</p>
            ) : (
              matched.map(event => (
                <div
                  key={event.id}
                  className="flex justify-between items-center py-3 border-b cursor-pointer hover:bg-muted rounded-md px-2"
                  onClick={() => setSelectedEvent(event)}
                >
                  <span className="text-sm font-medium">{event.name}</span>
                  <span className="text-sm font-mono">{CurrencyFormatter.format(Math.abs(event.amount))}</span>
                </div>
              ))
            )}
          </div>
        </SheetContent>
      </Sheet>
      {selectedEvent && (
        <EventDetailsModal
          show={true}
          event={selectedEvent}
          lineItemsForEvent={lineItemsForSelectedEvent}
          isLoadingLineItemsForEvent={isLoadingLineItems}
          onHide={() => setSelectedEvent(null)}
        />
      )}
    </>
  );
}
