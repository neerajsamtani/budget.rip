import * as React from "react"
import { createContext, useContext } from "react"
import { useMediaQuery } from "@/hooks/useMediaQuery"
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./dialog"
import { Sheet, SheetContent, SheetTitle, SheetDescription } from "./sheet"

const MobileContext = createContext(false)

function useIsMobile() {
  // Same as width < 768px; min/max-width also works in Safari before 16.4, unlike range syntax.
  return useMediaQuery("(max-width: 767.98px)")
}

interface ResponsiveDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
  className?: string
}

function ResponsiveDialog({ open, onOpenChange, children, className }: ResponsiveDialogProps) {
  const isMobile = useIsMobile()
  const mobileSheetStyle = { maxHeight: "min(90vh, calc(100dvh - 1rem))" }

  if (isMobile) {
    return (
      <MobileContext.Provider value={true}>
        <Sheet open={open} onOpenChange={onOpenChange}>
          <SheetContent
            side="bottom"
            className={`max-h-[90vh] overflow-y-auto overflow-x-hidden ${className || ""}`}
            style={mobileSheetStyle}
          >
            {children}
          </SheetContent>
        </Sheet>
      </MobileContext.Provider>
    )
  }

  return (
    <MobileContext.Provider value={false}>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className={`max-h-[90vh] overflow-y-auto overflow-x-hidden ${className || ""}`}>
          {children}
        </DialogContent>
      </Dialog>
    </MobileContext.Provider>
  )
}

function useResponsiveDialogContext() {
  return useContext(MobileContext)
}

function ResponsiveDialogTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  const isMobile = useContext(MobileContext)

  if (isMobile) {
    return <SheetTitle className={className}>{children}</SheetTitle>
  }

  return <DialogTitle className={className}>{children}</DialogTitle>
}

function ResponsiveDialogDescription({ children, className }: { children: React.ReactNode; className?: string }) {
  const isMobile = useContext(MobileContext)

  if (isMobile) {
    return <SheetDescription className={className}>{children}</SheetDescription>
  }

  return <DialogDescription className={className}>{children}</DialogDescription>
}

export {
  ResponsiveDialog,
  ResponsiveDialogTitle,
  ResponsiveDialogDescription,
  useIsMobile,
  useResponsiveDialogContext,
}
