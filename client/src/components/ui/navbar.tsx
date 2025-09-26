import React from "react"
import { cn } from "@/lib/utils"
import { NavigationMenu, NavigationMenuContent, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuTrigger } from "@/components/ui/navigation-menu"

export const Navbar = ({ children, className, ...props }: React.HTMLAttributes<HTMLElement>) => (
  <nav className={cn("border-b bg-background", className)} {...props}>
    {children}
  </nav>
)

export const NavbarBrand = ({ children, className, ...props }: React.HTMLAttributes<HTMLElement>) => (
  <div className={cn("font-semibold text-lg", className)} {...props}>
    {children}
  </div>
)