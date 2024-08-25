// Define a constant array for categories
export const CATEGORIES = [
    'All',
    'Alcohol',
    'Dining',
    'Entertainment',
    'Forma',
    'Groceries',
    'Hobbies',
    'Income',
    'Investment',
    'Rent',
    'Shopping',
    'Subscription',
    'Transfer',
    'Transit',
    'Travel'
] as const;

// Infer the Category type from the CATEGORIES array
export type Category = typeof CATEGORIES[number];