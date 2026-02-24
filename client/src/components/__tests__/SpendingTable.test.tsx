import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen, within } from '../../utils/test-utils';
import SpendingTable from '../charts/SpendingTable';

// Dining: Jan '24 has amount=50; Feb '24 has no entry (null)
// Shopping: Jan '24 has amount=100; Feb '24 has amount=0 (zero)
const data = {
  Dining: [{ date: '1-2024', amount: 50 }],
  Shopping: [{ date: '2-2024', amount: 0 }, { date: '1-2024', amount: 100 }],
};

const colorMap = { Dining: '#ff0000', Shopping: '#00ff00' };

function setup() {
  const onCellClick = jest.fn();
  render(<SpendingTable data={data} colorMap={colorMap} onCellClick={onCellClick} />);
  // rows[0]=header, rows[1]=Dining, rows[2]=Shopping, rows[3]=footer
  const rows = screen.getAllByRole('row');
  return { onCellClick, rows };
}

describe('SpendingTable', () => {
  it('non-zero cells call onCellClick(category, date) when clicked', async () => {
    const { onCellClick, rows } = setup();
    const diningRow = rows.find(row => within(row).queryByText('Dining'))!;
    // cells: [0]=category, [1]=Jan '24, [2]=Feb '24, [3]=Total
    const cells = within(diningRow).getAllByRole('cell');
    await userEvent.click(cells[1]);
    expect(onCellClick).toHaveBeenCalledWith('Dining', '1-2024');
  });

  it('zero-value cells show — and are not clickable', async () => {
    const { onCellClick, rows } = setup();
    const shoppingRow = rows.find(row => within(row).queryByText('Shopping'))!;
    const cells = within(shoppingRow).getAllByRole('cell');
    expect(cells[2]).toHaveTextContent('—');
    await userEvent.click(cells[2]);
    expect(onCellClick).not.toHaveBeenCalled();
  });

  it('null-value cells show — and are not clickable', async () => {
    const { onCellClick, rows } = setup();
    const diningRow = rows.find(row => within(row).queryByText('Dining'))!;
    const cells = within(diningRow).getAllByRole('cell');
    expect(cells[2]).toHaveTextContent('—');
    await userEvent.click(cells[2]);
    expect(onCellClick).not.toHaveBeenCalled();
  });

  it('row total cell calls onCellClick(category, "all") when clicked', async () => {
    const { onCellClick, rows } = setup();
    const diningRow = rows.find(row => within(row).queryByText('Dining'))!;
    const cells = within(diningRow).getAllByRole('cell');
    await userEvent.click(cells[cells.length - 1]);
    expect(onCellClick).toHaveBeenCalledWith('Dining', 'all');
  });

  it('column total cell calls onCellClick("all", date) when clicked', async () => {
    const { onCellClick, rows } = setup();
    const footerRow = rows[rows.length - 1];
    // cells: [0]="Total" label, [1]=Jan '24 col total (150, clickable), [2]=Feb '24 col total (0), [3]=grand total
    const cells = within(footerRow).getAllByRole('cell');
    await userEvent.click(cells[1]);
    expect(onCellClick).toHaveBeenCalledWith('all', '1-2024');
  });

  it('grand total cell always calls onCellClick("all", "all") when clicked', async () => {
    const { onCellClick, rows } = setup();
    const footerRow = rows[rows.length - 1];
    const cells = within(footerRow).getAllByRole('cell');
    await userEvent.click(cells[cells.length - 1]);
    expect(onCellClick).toHaveBeenCalledWith('all', 'all');
  });
});

describe('negative categories (income/investment)', () => {
  const incomeData = {
    Income: [
      { date: '1-2024', amount: -500 },
      { date: '2-2024', amount: -300 },
    ],
  };

  it('cell values display as negative', () => {
    const onCellClick = jest.fn();
    render(<SpendingTable data={incomeData} colorMap={{ Income: '#00ff00' }} onCellClick={onCellClick} />);
    const rows = screen.getAllByRole('row');
    const incomeRow = rows.find(row => within(row).queryByText('Income'))!;
    const cells = within(incomeRow).getAllByRole('cell');
    expect(cells[1]).toHaveTextContent('-$500.00');
  });

  it('row total displays as negative', () => {
    const onCellClick = jest.fn();
    render(<SpendingTable data={incomeData} colorMap={{ Income: '#00ff00' }} onCellClick={onCellClick} />);
    const rows = screen.getAllByRole('row');
    const incomeRow = rows.find(row => within(row).queryByText('Income'))!;
    const cells = within(incomeRow).getAllByRole('cell');
    expect(cells[cells.length - 1]).toHaveTextContent('-$800.00');
  });

  it('column total displays as negative', () => {
    const onCellClick = jest.fn();
    render(<SpendingTable data={incomeData} colorMap={{ Income: '#00ff00' }} onCellClick={onCellClick} />);
    const rows = screen.getAllByRole('row');
    const footerRow = rows[rows.length - 1];
    const cells = within(footerRow).getAllByRole('cell');
    // cells[1] = Jan '24 column total = -500
    expect(cells[1]).toHaveTextContent('-$500.00');
  });

  it('grand total displays as negative', () => {
    const onCellClick = jest.fn();
    render(<SpendingTable data={incomeData} colorMap={{ Income: '#00ff00' }} onCellClick={onCellClick} />);
    const rows = screen.getAllByRole('row');
    const footerRow = rows[rows.length - 1];
    const cells = within(footerRow).getAllByRole('cell');
    expect(cells[cells.length - 1]).toHaveTextContent('-$800.00');
  });
});
