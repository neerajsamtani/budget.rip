"use client"
import * as React from "react"
import { useSearchParams, usePathname, useRouter } from 'next/navigation';

import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

// Define a constant array for categories
const CATEGORIES = [
  'All',
  'Alcohol',
  'Dining',
  'Entertainment',
  'Forma',
  'Groceries',
  'Hobbies',
  'Income',
  'Investment',
  'Rent',
  'Shopping',
  'Subscription',
  'Transfer',
  'Transit',
  'Travel'
] as const;

// Infer the Category type from the CATEGORIES array
export type Category = typeof CATEGORIES[number];

export default function CategoryFilter() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const { replace } = useRouter();

  const [open, setOpen] = React.useState(false)
  const selectedCategory = searchParams.get('category')?.toString() || "All"

  function handleSelection(selection: Category) {
    const params = new URLSearchParams(searchParams);
    if (selection) {
      params.set('category', selection);
    } else {
      params.delete('category');
    }
    replace(`${pathname}?${params.toString()}`);
    setOpen(false)
  }

  return (
    <div className="flex items-center space-x-4">
      <p className="text-sm text-muted-foreground">Category</p>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-[150px] justify-start">
            {selectedCategory ? <>{selectedCategory}</> : <>+ Set category</>}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="p-0" side="right" align="start">
          <Command>
            <CommandInput placeholder="Change category..." />
            <CommandList>
              <CommandEmpty>No results found.</CommandEmpty>
              <CommandGroup>
                {CATEGORIES.map((category) => (
                  <CommandItem
                    key={category}
                    value={category}
                    onSelect={(value) => {
                      handleSelection(value as Category)
                    }}
                  >
                    {category}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  )
}
