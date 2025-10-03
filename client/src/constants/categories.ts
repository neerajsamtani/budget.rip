// Keep this in sync with the server/constants.py
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
  'Medical',
  'Rent',
  'Shopping',
  'Subscription',
  'Transfer',
  'Transit',
  'Travel'
] as const;

export type Category = typeof CATEGORIES[number];
