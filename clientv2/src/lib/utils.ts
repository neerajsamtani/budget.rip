import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import axios from "axios";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function toSentenceCase(str: string) {
  if (str.length === 0) {
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