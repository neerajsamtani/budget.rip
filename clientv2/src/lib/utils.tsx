import axios from "axios";
import { type ClassValue, clsx } from "clsx";
import type { LucideIcon } from "lucide-react";
import {
  ArrowLeftRight,
  Beer,
  Building2,
  Bus,
  Clapperboard,
  Home,
  PiggyBank,
  Plane,
  Popcorn,
  Repeat,
  ShoppingBag,
  ShoppingCart,
  TrendingUp,
  UtensilsCrossed
} from "lucide-react";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function toSentenceCase(str?: string) {
  if (str === undefined || str.length === 0) {
    return str; // Return the input if it's not a string or it's empty
  }

  // Capitalize the first character and lowercase the rest of the string
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export const axiosInstance = axios.create({
  withCredentials: true
})

export const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

export const dateFormatter = new Intl.DateTimeFormat('en-US', {
  dateStyle: 'medium',
});

export const category_to_icon_component = (category: string): React.ReactNode | null => {
  const iconMap: Record<string, LucideIcon> = {
    alcohol: Beer,
    dining: UtensilsCrossed,
    entertainment: Popcorn,
    forma: Building2,
    groceries: ShoppingCart,
    hobbies: Clapperboard,
    income: PiggyBank,
    investment: TrendingUp,
    rent: Home,
    shopping: ShoppingBag,
    subscription: Repeat,
    transfer: ArrowLeftRight,
    transit: Bus,
    travel: Plane
  };

  const IconComponent = iconMap[category.toLowerCase()]
  return IconComponent ? <IconComponent size={16} /> : null
}