import React from "react"
import { cn } from "@/lib/utils"

export const Spinner = ({ size = "sm", className, ...props }: { size?: "sm" | "md" | "lg", className?: string }) => (
  <div
    className={cn(
      "animate-spin rounded-full border-2 border-current border-t-transparent",
      size === "sm" && "h-4 w-4",
      size === "md" && "h-6 w-6",
      size === "lg" && "h-8 w-8",
      className
    )}
    {...props}
  />
)