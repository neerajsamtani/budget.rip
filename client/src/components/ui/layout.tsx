import React, { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface PageContainerProps {
  children: ReactNode;
  className?: string;
}

export function PageContainer({ children, className }: PageContainerProps) {
  return (
    <div className={cn(
      "container mx-auto px-4 md:px-6 py-6 md:py-8 max-w-7xl", // Nordic container specs with mobile optimization
      className
    )}>
      {children}
    </div>
  )
}

export function PageHeader({ children, className }: PageContainerProps) {
  return (
    <div className={cn("mb-8 space-y-2", className)}>
      {children}
    </div>
  )
}