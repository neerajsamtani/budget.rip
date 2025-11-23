import * as React from "react"
import { createContext, useContext, useEffect, useState } from "react"
import { Dialog, DialogContent } from "./dialog"
import { Sheet, SheetContent } from "./sheet"

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
          <SheetContent side="bottom" className={`max-h-[90vh] overflow-y-auto ${className || ""}`}>
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

export {
  ResponsiveDialog,
  useIsMobile,
  useResponsiveDialogContext,
}
