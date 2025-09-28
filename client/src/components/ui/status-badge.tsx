import { cn } from "@/lib/utils"

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'neutral';
  children: React.ReactNode;
  className?: string;
}

const statusStyles = {
  success: 'bg-[#ECFDF5] text-[#059669] border-[#059669]/20',
  warning: 'bg-[#FFFBEB] text-[#D97706] border-[#D97706]/20',
  error: 'bg-[#FEF2F2] text-[#DC2626] border-[#DC2626]/20',
  neutral: 'bg-[#F5F5F5] text-[#64748B] border-[#64748B]/20',
};

export function StatusBadge({ status, children, className }: StatusBadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border font-['Source_Sans_Pro']",
      statusStyles[status],
      className
    )}>
      {children}
    </span>
  )
}