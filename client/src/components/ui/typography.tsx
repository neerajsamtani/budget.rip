import { cn } from "@/lib/utils";
import React, { ReactNode } from "react";

interface TypographyProps {
  children: ReactNode;
  className?: string;
}

export function H1({ children, className }: TypographyProps) {
  return (
    <h1 className={cn("text-[36px] font-semibold leading-[1.2] tracking-[-0.01em]", "font-heading", className)}>
      {children}
    </h1>
  )
}

export function H3({ children, className }: TypographyProps) {
  return (
    <h3 className={cn("text-[22px] font-medium leading-[1.4]", "font-heading", className)}>
      {children}
    </h3>
  )
}

export function H4({ children, className }: TypographyProps) {
  return (
    <h4 className={cn("text-[18px] font-medium leading-[1.4]", "font-heading", className)}>
      {children}
    </h4>
  )
}

export function Body({ children, className }: TypographyProps) {
  return (
    <p className={cn("text-[16px] font-normal leading-[1.5]", "font-body", className)}>
      {children}
    </p>
  )
}