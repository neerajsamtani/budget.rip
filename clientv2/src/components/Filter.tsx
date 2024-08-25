"use client"
import * as React from "react"
import { useSearchParams, usePathname, useRouter } from 'next/navigation';
import { toSentenceCase } from "@/lib/utils";

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

export default function Filter({ paramName, options, defaultValue }: { paramName: string, options: readonly string[], defaultValue: string }) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const { replace } = useRouter();

  const [open, setOpen] = React.useState(false)
  const selectedValue = searchParams.get(paramName)?.toString() || defaultValue

  function handleSelection(selection: string) {
    const params = new URLSearchParams(searchParams);
    if (selection) {
      params.set(paramName, selection);
    } else {
      params.delete(paramName);
    }
    replace(`${pathname}?${params.toString()}`);
    setOpen(false)
  }

  return (
    <div className="flex items-center space-x-4">
      <p className="text-sm text-muted-foreground">{toSentenceCase(paramName)}</p>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-[150px] justify-start">
            {selectedValue ? <>{selectedValue}</> : <>{`+ Set ${paramName}`}</>}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="p-0" side="right" align="start">
          <Command>
            <CommandInput placeholder={`Change ${paramName}...`} />
            <CommandList>
              <CommandEmpty>No results found.</CommandEmpty>
              <CommandGroup>
                {options.map((option) => (
                  <CommandItem
                    key={option}
                    value={option}
                    onSelect={(value) => {
                      handleSelection(value)
                    }}
                  >
                    {option}
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
