import userEvent from '@testing-library/user-event';
import React, { useState } from 'react';
import { render, screen } from '../../utils/test-utils';
import MultiSelectFilter from '../MultiSelectFilter';

const TEST_OPTIONS = [
  { id: '1', name: 'Dining' },
  { id: '2', name: 'Groceries' },
  { id: '3', name: 'Entertainment' },
];
const ALL_NAMES = TEST_OPTIONS.map(o => o.name);

function MultiSelectFilterWrapper({ initialSelected = ALL_NAMES }: { initialSelected?: string[] }) {
  const [selected, setSelected] = useState<string[]>(initialSelected);
  return (
    <MultiSelectFilter
      label="Category"
      options={TEST_OPTIONS}
      selected={selected}
      onChange={setSelected}
    />
  );
}

function getTrigger() {
  return screen.getByRole('button');
}

describe('MultiSelectFilter', () => {
  describe('Rendering — "All" label', () => {
    it('trigger displays "All" when all options are selected', () => {
      render(<MultiSelectFilterWrapper initialSelected={ALL_NAMES} />);
      expect(getTrigger()).toHaveTextContent('All');
    });

    it('trigger displays comma-separated names when a subset is selected', () => {
      render(<MultiSelectFilterWrapper initialSelected={['Dining', 'Groceries']} />);
      expect(getTrigger()).toHaveTextContent('Dining, Groceries');
    });

    it('trigger shows the label placeholder when no options are selected', () => {
      render(<MultiSelectFilterWrapper initialSelected={[]} />);
      expect(getTrigger()).toHaveTextContent('Category');
    });
  });

  describe('X button visibility', () => {
    it('X button is not shown when all options are selected', () => {
      render(<MultiSelectFilterWrapper initialSelected={ALL_NAMES} />);
      expect(screen.queryByTestId('clear-selection')).not.toBeInTheDocument();
    });

    it('X button is shown when a subset of options is selected', () => {
      render(<MultiSelectFilterWrapper initialSelected={['Dining']} />);
      expect(screen.getByTestId('clear-selection')).toBeInTheDocument();
    });
  });

  describe('Clear button behavior', () => {
    it('clicking X when a subset is selected calls onChange with all option names', async () => {
      const onChange = jest.fn();
      render(
        <MultiSelectFilter
          label="Category"
          options={TEST_OPTIONS}
          selected={['Dining']}
          onChange={onChange}
        />
      );
      await userEvent.click(screen.getByTestId('clear-selection'));
      expect(onChange).toHaveBeenCalledWith(ALL_NAMES);
    });

    it('after clicking X, trigger displays "All" and X button disappears', async () => {
      render(<MultiSelectFilterWrapper initialSelected={['Dining']} />);
      expect(getTrigger()).toHaveTextContent('Dining');

      await userEvent.click(screen.getByTestId('clear-selection'));

      expect(getTrigger()).toHaveTextContent('All');
      expect(screen.queryByTestId('clear-selection')).not.toBeInTheDocument();
    });
  });
});
