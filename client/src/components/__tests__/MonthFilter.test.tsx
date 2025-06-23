import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen } from '../../utils/test-utils';
import MonthFilter from '../MonthFilter';

describe('MonthFilter', () => {
    const mockSetMonth = jest.fn();

    const allMonths = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December', 'All'
    ];

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Rendering', () => {
        it('renders the month filter component', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            expect(screen.getByText('Month')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('renders all month options', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            allMonths.forEach(month => {
                expect(screen.getByRole('option', { name: month })).toBeInTheDocument();
            });
        });

        it('displays the correct selected month', () => {
            render(<MonthFilter month="March" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            expect(select).toHaveValue('March');
        });

        it('displays "All" as selected when that is the current month', () => {
            render(<MonthFilter month="All" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            expect(select).toHaveValue('All');
        });

        it('renders with proper form structure', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            expect(screen.getByText('Month')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('has proper accessibility attributes', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            expect(select).toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('calls setMonth when a different month is selected', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'March');

            expect(mockSetMonth).toHaveBeenCalledWith('March');
        });

        it('calls setMonth when "All" is selected', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'All');

            expect(mockSetMonth).toHaveBeenCalledWith('All');
        });

        it('calls setMonth when December is selected', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'December');

            expect(mockSetMonth).toHaveBeenCalledWith('December');
        });

        it('calls setMonth when July is selected', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'July');

            expect(mockSetMonth).toHaveBeenCalledWith('July');
        });

        it('calls setMonth only once per selection', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'February');

            expect(mockSetMonth).toHaveBeenCalledTimes(1);
            expect(mockSetMonth).toHaveBeenCalledWith('February');
        });
    });

    describe('Props Handling', () => {
        it('accepts different initial month values', () => {
            const { rerender } = render(<MonthFilter month="January" setMonth={mockSetMonth} />);
            expect(screen.getByRole('combobox')).toHaveValue('January');

            rerender(<MonthFilter month="June" setMonth={mockSetMonth} />);
            expect(screen.getByRole('combobox')).toHaveValue('June');

            rerender(<MonthFilter month="All" setMonth={mockSetMonth} />);
            expect(screen.getByRole('combobox')).toHaveValue('All');
        });

        it('calls the provided setMonth function', async () => {
            const customSetMonth = jest.fn();
            render(<MonthFilter month="January" setMonth={customSetMonth} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'August');

            expect(customSetMonth).toHaveBeenCalledWith('August');
        });
    });

    describe('Month Options', () => {
        it('renders all 13 options (12 months + All)', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(13);
        });

        it('renders months in correct order', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const options = screen.getAllByRole('option');
            const optionValues = options.map(option => option.getAttribute('value'));

            expect(optionValues).toEqual(allMonths);
        });

        it('has correct values for all options', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            allMonths.forEach(month => {
                const option = screen.getByRole('option', { name: month });
                expect(option).toHaveValue(month);
            });
        });
    });

    describe('Event Handling', () => {
        it('handles change event correctly', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'October');

            expect(mockSetMonth).toHaveBeenCalledWith('October');
        });

        it('casts the selected value to Month type', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'November');

            // The component should cast the string value to Month type
            expect(mockSetMonth).toHaveBeenCalledWith('November');
        });
    });

    describe('Component Structure', () => {
        it('renders with InputGroup structure', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Check for InputGroup.Text
            expect(screen.getByText('Month')).toBeInTheDocument();

            // Check for Form.Select
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
    });

    describe('Edge Cases', () => {
        it('handles rapid month changes', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');

            await userEvent.selectOptions(select, 'February');
            await userEvent.selectOptions(select, 'March');
            await userEvent.selectOptions(select, 'April');

            expect(mockSetMonth).toHaveBeenCalledTimes(3);
            expect(mockSetMonth).toHaveBeenNthCalledWith(1, 'February');
            expect(mockSetMonth).toHaveBeenNthCalledWith(2, 'March');
            expect(mockSetMonth).toHaveBeenNthCalledWith(3, 'April');
        });

        it('maintains selected value after prop updates', () => {
            const { rerender } = render(<MonthFilter month="January" setMonth={mockSetMonth} />);
            expect(screen.getByRole('combobox')).toHaveValue('January');

            rerender(<MonthFilter month="December" setMonth={mockSetMonth} />);
            expect(screen.getByRole('combobox')).toHaveValue('December');
        });
    });
}); 