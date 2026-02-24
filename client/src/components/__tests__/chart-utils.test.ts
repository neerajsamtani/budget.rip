import {
  filterByCategories,
  filterByYear,
  formatMonthYear,
  getAvailableYears,
  toRowPerDate,
} from '../charts/chart-utils';

describe('formatMonthYear', () => {
  it('"1-2023" formats as "Jan \'23"', () => {
    expect(formatMonthYear('1-2023')).toBe("Jan '23");
  });

  it('"12-2024" formats as "Dec \'24"', () => {
    expect(formatMonthYear('12-2024')).toBe("Dec '24");
  });
});

describe('getAvailableYears', () => {
  it('returns sorted unique years from data spanning multiple years', () => {
    const data = {
      Dining: [{ date: '1-2023', amount: 100 }, { date: '3-2024', amount: 200 }],
      Shopping: [{ date: '5-2023', amount: 50 }, { date: '2-2022', amount: 75 }],
    };
    expect(getAvailableYears(data)).toEqual(['2022', '2023', '2024']);
  });

  it('returns empty array for empty data', () => {
    expect(getAvailableYears({})).toEqual([]);
  });
});

describe('filterByYear', () => {
  const data = {
    Dining: [{ date: '1-2023', amount: 100 }, { date: '1-2024', amount: 200 }],
    Shopping: [{ date: '3-2024', amount: 50 }],
  };

  it('keeps only entries matching the given year', () => {
    expect(filterByYear(data, '2023')).toEqual({
      Dining: [{ date: '1-2023', amount: 100 }],
    });
  });

  it('drops categories with no entries in that year', () => {
    expect(filterByYear(data, '2023')).not.toHaveProperty('Shopping');
  });
});

describe('filterByCategories', () => {
  const data = {
    Dining: [{ date: '1-2024', amount: 100 }],
    Shopping: [{ date: '1-2024', amount: 50 }],
    Travel: [{ date: '1-2024', amount: 200 }],
  };

  it('keeps only the specified categories', () => {
    const result = filterByCategories(data, ['Dining', 'Travel']);
    expect(Object.keys(result)).toEqual(['Dining', 'Travel']);
  });

  it('empty array returns all categories unchanged', () => {
    expect(filterByCategories(data, [])).toBe(data);
  });
});

describe('toRowPerDate', () => {
  const data = {
    Dining: [{ date: '1-2023', amount: 100 }, { date: '2-2023', amount: 150 }],
    Shopping: [{ date: '1-2023', amount: 200 }],
  };

  it('merges multiple categories into one row per date', () => {
    const rows = toRowPerDate(data);
    const janRow = rows.find(r => r.date === '1-2023');
    expect(janRow).toMatchObject({ Dining: 100, Shopping: 200 });
  });

  it('rows are sorted chronologically (year first, then month)', () => {
    const multiYearData = {
      Dining: [
        { date: '3-2023', amount: 100 },
        { date: '1-2022', amount: 50 },
        { date: '11-2022', amount: 75 },
      ],
    };
    const rows = toRowPerDate(multiYearData);
    expect(rows.map(r => r.date)).toEqual(['1-2022', '11-2022', '3-2023']);
  });

  it('adds formattedDate field to each row', () => {
    const rows = toRowPerDate(data);
    const janRow = rows.find(r => r.date === '1-2023');
    expect(janRow?.formattedDate).toBe("Jan '23");
  });
});
