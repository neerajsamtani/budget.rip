import { CATEGORIES, MONTHS, YEARS } from "./constants";

// Infer the Category type from the CATEGORIES array
export type Category = typeof CATEGORIES[number];

// Infer the Year type from the YEARS array
export type Year = typeof YEARS[number];

// Infer the Year type from the YEARS array
export type Month = typeof MONTHS[number];

export interface LineItemInterface {
    _id: string;
    id: string;
    date: number; // Assuming date is a UNIX timestamp in seconds
    payment_method: string;
    description: string;
    responsible_party: string;
    amount: number;
    isSelected?: boolean; // Optional if not used in this context
}