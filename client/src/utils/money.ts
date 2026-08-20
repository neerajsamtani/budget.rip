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

  // Scaling by 100 is inexact in binary floating point (76.10 * 100 is
  // 7609.999999999999), so round to the whole cent the input names. The value
  // is already capped at two decimals, making the rounding lossless.
  const cents = Math.round(amount * 100);
  return Number.isSafeInteger(cents) ? cents : null;
}
