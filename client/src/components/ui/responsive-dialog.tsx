import * as React from "react"
import { createContext, useContext, useEffect, useState } from "react"
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./dialog"
import { Sheet, SheetContent, SheetTitle, SheetDescription } from "./sheet"

const MobileContext = createContext(false)

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
      <MobileContext.Provider value={true}>
        <Sheet open={open} onOpenChange={onOpenChange}>
          <SheetContent side="bottom" className={`max-h-[90vh] overflow-y-auto overflow-x-hidden ${className || ""}`}>
            {children}
          </SheetContent>
        </Sheet>
      </MobileContext.Provider>
    )
  }

  return (
    <MobileContext.Provider value={false}>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className={className}>
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
