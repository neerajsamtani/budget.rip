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

export function toTitleCase(str?: string) {
  if (str === undefined || str.length === 0) {
    return str; // Return the input if it's not a string or it's empty
  }

  // Split the string into words and capitalize the first letter of each word
  return str.split(/[\s_\-]+/).map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
}

export function toKebabCase(str: string) {
  return str.toLowerCase().replace(/\s+/g, '-');
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