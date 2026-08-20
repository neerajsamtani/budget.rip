import { parseMoneyToCents } from '../money';

describe('parseMoneyToCents', () => {
  it.each([
    ['42', 4200],
    ['42.3', 4230],
    ['42.35', 4235],
    ['.5', 50],
    [' 10.00 ', 1000],
    // Amounts whose scaled value is inexact in binary floating point
    ['76.10', 7610],
    ['38.05', 3805],
    ['1.10', 110],
    ['0.07', 7],
  ])('converts %s to cents', (value, expectedCents) => {
    expect(parseMoneyToCents(value)).toBe(expectedCents);
  });

  it.each([
    '',
    '-1',
    '1.234',
    '1.2.3',
    '1e2',
    '0x10',
    'Infinity',
    '999999999999999999',
  ])('rejects invalid monetary amount %s', (value) => {
    expect(parseMoneyToCents(value)).toBeNull();
  });
});
