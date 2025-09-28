import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-150 disabled:pointer-events-none disabled:opacity-50 outline-none focus-visible:ring-2 focus-visible:ring-offset-2 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Primary Nordic Blue button
        default: "bg-[#5B82C4] text-white hover:bg-[#3D5A96] focus-visible:ring-[#5B82C4]",

        // Secondary Nordic button
        secondary: "bg-transparent text-[#5B82C4] border border-[#5B82C4] hover:bg-[#E8F0FE] focus-visible:ring-[#5B82C4]",

        // Ghost Nordic button
        ghost: "bg-transparent text-[#374151] hover:bg-[#F5F5F5] focus-visible:ring-[#6B7280]",

        // Destructive button
        destructive: "bg-[#DC2626] text-white hover:bg-[#B91C1C] focus-visible:ring-[#DC2626]",

        // Link button
        link: "text-[#5B82C4] underline-offset-4 hover:underline focus-visible:ring-[#5B82C4]",
      },
      size: {
        default: "h-12 px-5 py-3", // 12px vertical, 20px horizontal per Nordic specs
        sm: "h-10 px-4 py-2",
        lg: "h-14 px-6 py-4",
        icon: "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
