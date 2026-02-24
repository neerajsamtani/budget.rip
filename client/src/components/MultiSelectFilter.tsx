import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ChevronDown, XCircle } from 'lucide-react';
import React, { useState } from 'react';

const MAX_DISPLAY = 5;

interface MultiSelectFilterProps {
  label: string;
  options: { id: string; name: string }[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

export default function MultiSelectFilter({ label, options, selected, onChange }: MultiSelectFilterProps) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<string[]>([]);

  const hasSelections = selected.length > 0;
  const sortedSelected = [...selected].sort();

  function handleOpenChange(nextOpen: boolean) {
    if (nextOpen) setPending(selected);
    setOpen(nextOpen);
  }

  function togglePending(name: string) {
    setPending(prev => prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]);
  }

  function handleApply() {
    onChange(pending);
    setOpen(false);
  }

  function handleClear(e: React.MouseEvent) {
    e.stopPropagation();
    onChange(options.map(o => o.name));
  }

  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <Popover open={open} onOpenChange={handleOpenChange}>
        <PopoverTrigger asChild>
          <button className="border-input flex h-11 w-fit items-center gap-2 rounded-md border bg-transparent px-3 py-2 text-base whitespace-nowrap shadow-xs transition-colors outline-none focus-visible:ring-2">
            <span className={hasSelections ? 'text-foreground' : 'text-muted-foreground'}>
              {selected.length === options.length && options.length > 0
                ? 'All'
                : hasSelections
                  ? sortedSelected.length > MAX_DISPLAY
                    ? `${sortedSelected.slice(0, MAX_DISPLAY).join(', ')} +${sortedSelected.length - MAX_DISPLAY} more`
                    : sortedSelected.join(', ')
                  : label}
            </span>
            {selected.length > 0 && selected.length < options.length && (
              <XCircle
                data-testid="clear-selection"
                className="size-4 shrink-0 text-muted-foreground transition-colors hover:text-destructive"
                onClick={handleClear}
              />
            )}
            <ChevronDown data-testid="chevron-down" className="size-4 shrink-0 opacity-50" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-64 p-0" align="start">
          <div className="border-b px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Filter by: {label}
          </div>
          <div className="max-h-60 overflow-y-auto py-1">
            <label className="flex cursor-pointer items-center gap-2 border-b px-3 py-2 text-sm font-medium hover:bg-muted">
              <Checkbox
                checked={pending.length === options.length ? true : pending.length === 0 ? false : 'indeterminate'}
                onCheckedChange={checked => setPending(checked ? options.map(o => o.name) : [])}
              />
              Select all
            </label>
            {options.map(opt => (
              <label
                key={opt.id}
                className="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-muted"
              >
                <Checkbox
                  checked={pending.includes(opt.name)}
                  onCheckedChange={() => togglePending(opt.name)}
                />
                {opt.name}
              </label>
            ))}
          </div>
          <div className="border-t p-2">
            <button
              onClick={handleApply}
              className="w-full rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Apply
            </button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
