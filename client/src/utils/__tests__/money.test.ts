import { parseMoneyToCents } from '../money';

describe('parseMoneyToCents', () => {
  it.each([
    ['42', 4200],
    ['42.3', 4230],
    ['42.35', 4235],
    ['.5', 50],
    [' 10.00 ', 1000],
    ['19.99', 1999],
    ['0.29', 29],
    ['1.15', 115],
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
  ])('rejects invalid monetary amount %s', (value) => {
    expect(parseMoneyToCents(value)).toBeNull();
  });
});
