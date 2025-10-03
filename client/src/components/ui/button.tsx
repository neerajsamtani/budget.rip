import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import * as React from "react"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-150 hover:cursor-pointer disabled:pointer-events-none disabled:opacity-50 outline-none focus-visible:ring-2 focus-visible:ring-offset-2 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Primary Nordic Blue button
        default: "bg-primary text-white hover:bg-primary-dark focus-visible:ring-primary",

        // Secondary Nordic button
        secondary: "bg-transparent text-primary border border-primary hover:bg-primary-light focus-visible:ring-primary",

        // Ghost Nordic button
        ghost: "bg-transparent text-foreground hover:bg-muted focus-visible:ring-muted-foreground",

        // Destructive button
        destructive: "bg-semantic-error text-white hover:bg-semantic-error-dark focus-visible:ring-semantic-error",

        // Link button
        link: "text-primary underline-offset-4 hover:underline focus-visible:ring-primary",
      },
      size: {
        default: "h-12 px-6 py-3", // 12px vertical, 24px horizontal per Nordic specs
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
