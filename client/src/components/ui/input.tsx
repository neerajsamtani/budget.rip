import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        // Nordic input specifications
        "w-full rounded-md border bg-white px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground",
        "font-body min-w-0",
        "focus:border-primary focus:ring-2 focus:ring-primary-light focus:outline-none",
        "disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed",
        "transition-colors duration-150",
        "file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
        "selection:bg-primary selection:text-white",
        className
      )}
      {...props}
    />
  )
}

export { Input }
