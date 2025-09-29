import React, { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface PageContainerProps {
  children: ReactNode;
  className?: string;
}

export function PageContainer({ children, className }: PageContainerProps) {
  return (
    <div className={cn(
      "container mx-auto px-6 py-8 max-w-7xl", // Nordic container specs
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

export function ContentGrid({ children, className }: PageContainerProps) {
  return (
    <div className={cn(
      "grid grid-cols-1 lg:grid-cols-12 gap-6", // Nordic 12-column grid
      className
    )}>
      {children}
    </div>
  )
}

export function MainContent({ children, className }: PageContainerProps) {
  return (
    <div className={cn("lg:col-span-8", className)}> {/* 60% width on desktop */}
      {children}
    </div>
  )
}

export function Sidebar({ children, className }: PageContainerProps) {
  return (
    <div className={cn("lg:col-span-4", className)}> {/* 30% width on desktop */}
      {children}
    </div>
  )
}