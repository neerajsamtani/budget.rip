import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        // Nordic input specifications
        // Use text-base (16px) to prevent iOS zoom on focus
        "w-full max-w-full rounded-md border bg-white px-4 py-3 text-base text-foreground placeholder:text-muted-foreground",
        "font-body min-w-0 box-border",
        "focus:border-primary focus:ring-2 focus:ring-primary-light focus:outline-none",
        "disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed",
        "transition-colors duration-150",
        "file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-base file:font-medium file:text-foreground",
        "selection:bg-primary selection:text-white",
        // Date input specific styling to prevent overflow
        type === "date" && "appearance-none",
        className
      )}
      {...props}
    />
  )
}

export { Input }
