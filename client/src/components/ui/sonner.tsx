"use client"

import React from "react";
import { Toaster as Sonner, ToasterProps } from "sonner";

// Mock useTheme for non-Next.js apps or provide a simple theme fallback
const useTheme = () => ({ theme: "light" });

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "light" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      {...props}
    />
  )
}

export { Toaster };

