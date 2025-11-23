import * as React from "react"
import { useEffect, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./dialog"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "./sheet"

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener("resize", checkMobile)
    return () => window.removeEventListener("resize", checkMobile)
  }, [])

  return isMobile
}

interface ResponsiveDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
  className?: string
}

function ResponsiveDialog({ open, onOpenChange, children, className }: ResponsiveDialogProps) {
  const isMobile = useIsMobile()

  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="bottom" className={`max-h-[90vh] overflow-y-auto ${className || ""}`}>
          {children}
        </SheetContent>
      </Sheet>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={className}>
        {children}
      </DialogContent>
    </Dialog>
  )
}

interface ResponsiveDialogHeaderProps {
  children: React.ReactNode
  className?: string
}

function ResponsiveDialogHeader({ children, className }: ResponsiveDialogHeaderProps) {
  const isMobile = useIsMobile()

  if (isMobile) {
    return <SheetHeader className={className}>{children}</SheetHeader>
  }

  return <DialogHeader className={className}>{children}</DialogHeader>
}

interface ResponsiveDialogTitleProps {
  children: React.ReactNode
  className?: string
}

function ResponsiveDialogTitle({ children, className }: ResponsiveDialogTitleProps) {
  const isMobile = useIsMobile()

  if (isMobile) {
    return <SheetTitle className={className}>{children}</SheetTitle>
  }

  return <DialogTitle className={className}>{children}</DialogTitle>
}

interface ResponsiveDialogDescriptionProps {
  children: React.ReactNode
  className?: string
}

function ResponsiveDialogDescription({ children, className }: ResponsiveDialogDescriptionProps) {
  const isMobile = useIsMobile()

  if (isMobile) {
    return <SheetDescription className={className}>{children}</SheetDescription>
  }

  return <DialogDescription className={className}>{children}</DialogDescription>
}

interface ResponsiveDialogFooterProps {
  children: React.ReactNode
  className?: string
}

function ResponsiveDialogFooter({ children, className }: ResponsiveDialogFooterProps) {
  const isMobile = useIsMobile()

  if (isMobile) {
    return <SheetFooter className={className}>{children}</SheetFooter>
  }

  return <DialogFooter className={className}>{children}</DialogFooter>
}

export {
  ResponsiveDialog,
  ResponsiveDialogHeader,
  ResponsiveDialogTitle,
  ResponsiveDialogDescription,
  ResponsiveDialogFooter,
  useIsMobile,
}
