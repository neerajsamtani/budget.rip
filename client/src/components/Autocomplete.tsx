import {
  CommandGroup,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { Command as CommandPrimitive } from "cmdk"
import { Check } from "lucide-react"
import React, { useCallback, useRef, useState, type KeyboardEvent } from "react"

export type Option = Record<"value" | "label", string> & Record<string, string>

type AutoCompleteProps = {
  options: Option[]
  value?: Option
  // eslint-disable-next-line no-unused-vars
  onValueChange?: (value: Option | undefined) => void
  isLoading?: boolean
  disabled?: boolean
  placeholder?: string
  allowCreate?: boolean
  clearOnSelect?: boolean
}

export const AutoComplete = ({
  options,
  placeholder,
  value,
  onValueChange,
  disabled,
  isLoading = false,
  allowCreate = false,
  clearOnSelect = false,
}: AutoCompleteProps) => {
  const inputRef = useRef<HTMLInputElement>(null)

  const [isOpen, setOpen] = useState(false)
  const [selected, setSelected] = useState<Option | undefined>(value)
  const [inputValue, setInputValue] = useState<string>(value?.label || "")

  const selectOption = useCallback(
    (option: Option, shouldBlur = false) => {
      onValueChange?.(option)
      if (clearOnSelect) {
        setInputValue("")
        setSelected(undefined)
      } else {
        setInputValue(option.label)
        setSelected(option)
        if (shouldBlur) {
          setTimeout(() => inputRef?.current?.blur(), 0)
        }
      }
    },
    [onValueChange, clearOnSelect],
  )

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      const input = inputRef.current
      if (!input) return

      if (!isOpen && inputValue.length > 0) {
        setOpen(true)
      }

      if (event.key === "Enter" && input.value !== "") {
        event.preventDefault()
        const existingOption = options.find((option) => option.label === input.value)
        const optionToSelect = existingOption || (allowCreate && input.value.trim()
          ? { value: input.value.trim(), label: input.value.trim() }
          : null)
        if (optionToSelect) {
          selectOption(optionToSelect)
        }
      }

      if (event.key === "Escape") {
        input.blur()
        setOpen(false)
      }
    },
    [isOpen, options, allowCreate, inputValue, selectOption],
  )

  const handleBlur = useCallback(() => {
    setOpen(false)
    if (!clearOnSelect && selected) {
      setInputValue(selected.label)
    }
  }, [selected, clearOnSelect])

  const handleSelectOption = useCallback(
    (selectedOption: Option) => selectOption(selectedOption, true),
    [selectOption],
  )

  const shouldShowDropdown = isOpen && inputValue.length > 0 && (options.length > 0 || isLoading)

  return (
    <CommandPrimitive onKeyDown={handleKeyDown} className="relative">
      <CommandPrimitive.Input
        ref={inputRef}
        value={inputValue}
        onValueChange={(newValue) => {
          if (!isLoading) {
            setInputValue(newValue)
            if (newValue === "" && !clearOnSelect) {
              setSelected(undefined)
              onValueChange?.(undefined)
            }
          }
        }}
        onBlur={handleBlur}
        onFocus={() => inputValue.length > 0 && setOpen(true)}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          "w-full max-w-full rounded-md border bg-white px-4 text-base text-foreground placeholder:text-muted-foreground h-11",
          "font-body min-w-0 box-border",
          "focus:border-primary focus:ring-2 focus:ring-primary-light focus:outline-none",
          "disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed",
          "transition-colors duration-150"
        )}
      />
      {shouldShowDropdown && (
        <div className="animate-in fade-in-0 zoom-in-95 absolute top-full mt-1 z-10 w-full rounded-xl bg-white outline-none">
          <CommandList className="rounded-lg ring-1 ring-slate-200">
            {isLoading ? (
              <CommandPrimitive.Loading>
                <div className="p-1">
                  <Skeleton className="h-8 w-full" />
                </div>
              </CommandPrimitive.Loading>
            ) : null}
            {options.length > 0 && !isLoading ? (
              <CommandGroup>
                {options.map((option) => {
                  const isSelected = selected?.value === option.value
                  return (
                    <CommandItem
                      key={option.value}
                      value={option.label}
                      onMouseDown={(event) => {
                        event.preventDefault()
                        event.stopPropagation()
                      }}
                      onSelect={() => handleSelectOption(option)}
                      className={cn(
                        "flex w-full items-center gap-2",
                        !isSelected ? "pl-8" : null,
                      )}
                    >
                      {isSelected ? <Check className="w-4" /> : null}
                      {option.label}
                    </CommandItem>
                  )
                })}
              </CommandGroup>
            ) : null}
          </CommandList>
        </div>
      )}
    </CommandPrimitive>
  )
}
