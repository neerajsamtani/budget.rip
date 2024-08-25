import { CATEGORIES, MONTHS, YEARS } from "./constants";

// Infer the Category type from the CATEGORIES array
export type Category = typeof CATEGORIES[number];

// Infer the Year type from the YEARS array
export type Year = typeof YEARS[number];

// Infer the Year type from the YEARS array
export type Month = typeof MONTHS[number];