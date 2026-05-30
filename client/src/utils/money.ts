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

  const cents = amount * 100;
  return Number.isSafeInteger(cents) ? cents : null;
}
