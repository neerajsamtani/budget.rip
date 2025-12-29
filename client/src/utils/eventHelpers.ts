import { LineItemInterface } from '../contexts/LineItemsContext';

/**
 * Calculate the total amount for an event based on its line items
 * and whether it's a duplicate transaction.
 */
export function calculateEventTotal(
  lineItems: LineItemInterface[],
  isDuplicateTransaction: boolean
): number {
  if (lineItems.length === 0) return 0;
  if (isDuplicateTransaction) return lineItems[0].amount;
  return lineItems.reduce((sum, item) => sum + item.amount, 0);
}
