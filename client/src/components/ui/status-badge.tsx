import React from "react"
import { cn } from "@/lib/utils"

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'neutral';
  children: React.ReactNode;
  className?: string;
}

const statusStyles = {
  success: 'bg-green-50 text-green-600 border-green-600/20',
  warning: 'bg-yellow-50 text-yellow-600 border-yellow-600/20',
  error: 'bg-red-50 text-semantic-error border-semantic-error/20',
  neutral: 'bg-muted text-muted-foreground border-muted-foreground/20',
};

export function StatusBadge({ status, children, className }: StatusBadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border font-body",
      statusStyles[status],
      className
    )}>
      {children}
    </span>
  )
}