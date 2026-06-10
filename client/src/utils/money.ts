export function parseMoneyToCents(value: string): number | null {
  const normalizedValue = value.trim();
  const decimalParts = normalizedValue.split(".");
  const amount = Number(normalizedValue);
  const hasOnlyDigitsAndDecimalPoint = [...normalizedValue].every(
    character => character === "." || (character >= "0" && character <= "9")
  );

  if (
    !normalizedValue
    || !hasOnlyDigitsAndDecimalPoint
    || decimalParts.length > 2
    || (decimalParts[1]?.length ?? 0) > 2
    || !Number.isFinite(amount)
    || amount < 0
  ) {
    return null;
  }

  // Input is validated to <=2 decimals, so rounding only corrects float error
  // (e.g. 19.99 * 100 === 1998.9999...).
  const cents = Math.round(amount * 100);
  return Number.isSafeInteger(cents) ? cents : null;
}
