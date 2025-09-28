import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        // Nordic input specifications
        "w-full rounded-md border border-[#E0E0E0] bg-white px-4 py-3 text-sm text-[#374151] placeholder:text-[#6B7280]",
        "font-['Source_Sans_Pro'] min-w-0",
        "focus:border-[#5B82C4] focus:ring-2 focus:ring-[#E8F0FE] focus:outline-none",
        "disabled:bg-[#F5F5F5] disabled:text-[#6B7280] disabled:cursor-not-allowed",
        "transition-colors duration-150",
        "file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[#374151]",
        "selection:bg-[#5B82C4] selection:text-white",
        className
      )}
      {...props}
    />
  )
}

export { Input }
