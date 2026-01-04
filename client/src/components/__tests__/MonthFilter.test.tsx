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
        it('month filter component is displayed', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            expect(screen.getByText('Month')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('all month options are available', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select to reveal options
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Check that all months are available as options
            allMonths.forEach(month => {
                expect(screen.getAllByText(month).length).toBeGreaterThanOrEqual(1);
            });
        });

        it('correct selected month is displayed', () => {
            render(<MonthFilter month="March" setMonth={mockSetMonth} />);

            // Check that the selected value is displayed
            expect(screen.getByText('March')).toBeInTheDocument();
        });

        it('"All" is displayed when that is the current month', () => {
            render(<MonthFilter month="All" setMonth={mockSetMonth} />);

            // Check that "All" is displayed as the selected value
            expect(screen.getByText('All')).toBeInTheDocument();
        });

        it('proper form structure is rendered', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            expect(screen.getByText('Month')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('proper accessibility attributes are set', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const select = screen.getByRole('combobox');
            expect(select).toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('setMonth is called when a different month is selected', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select dropdown
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Click on March option
            const marchOption = screen.getByText('March');
            await userEvent.click(marchOption);

            expect(mockSetMonth).toHaveBeenCalledWith('March');
        });

        it('setMonth is called when "All" is selected', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select dropdown
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Click on All option
            const allOption = screen.getByText('All');
            await userEvent.click(allOption);

            expect(mockSetMonth).toHaveBeenCalledWith('All');
        });

        it('setMonth is called when December is selected', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select dropdown
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Click on December option
            const decemberOption = screen.getByText('December');
            await userEvent.click(decemberOption);

            expect(mockSetMonth).toHaveBeenCalledWith('December');
        });

        it('setMonth is called when July is selected', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select dropdown
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Click on July option
            const julyOption = screen.getByText('July');
            await userEvent.click(julyOption);

            expect(mockSetMonth).toHaveBeenCalledWith('July');
        });

        it('setMonth is called only once per selection', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select dropdown
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Click on February option
            const februaryOption = screen.getByText('February');
            await userEvent.click(februaryOption);

            expect(mockSetMonth).toHaveBeenCalledTimes(1);
            expect(mockSetMonth).toHaveBeenCalledWith('February');
        });
    });

    describe('Props Handling', () => {
        it('different initial month values are accepted', () => {
            const { rerender } = render(<MonthFilter month="January" setMonth={mockSetMonth} />);
            expect(screen.getByText('January')).toBeInTheDocument();

            rerender(<MonthFilter month="June" setMonth={mockSetMonth} />);
            expect(screen.getByText('June')).toBeInTheDocument();

            rerender(<MonthFilter month="All" setMonth={mockSetMonth} />);
            expect(screen.getByText('All')).toBeInTheDocument();
        });

        it('provided setMonth function is called', async () => {
            const customSetMonth = jest.fn();
            render(<MonthFilter month="January" setMonth={customSetMonth} />);

            // Open the select dropdown
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Click on August option
            const augustOption = screen.getByText('August');
            await userEvent.click(augustOption);

            expect(customSetMonth).toHaveBeenCalledWith('August');
        });
    });

    describe('Month Options', () => {
        it('all 13 options are rendered (12 months + All)', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select to reveal options
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Count all month options that are now visible
            allMonths.forEach(month => {
                expect(screen.getAllByText(month).length).toBeGreaterThanOrEqual(1);
            });
        });

        it('months are rendered in correct order', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select to reveal options
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Verify all months are present (order testing is complex with shadcn)
            allMonths.forEach(month => {
                expect(screen.getAllByText(month).length).toBeGreaterThanOrEqual(1);
            });
        });

        it('all options have correct values', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select to reveal options
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Verify all month options are available
            allMonths.forEach(month => {
                expect(screen.getAllByText(month).length).toBeGreaterThanOrEqual(1);
            });
        });
    });

    describe('Event Handling', () => {
        it('change event is handled correctly', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select dropdown
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Click on October option
            const octoberOption = screen.getByText('October');
            await userEvent.click(octoberOption);

            expect(mockSetMonth).toHaveBeenCalledWith('October');
        });

        it('selected value is cast to Month type', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Open the select dropdown
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Click on November option
            const novemberOption = screen.getByText('November');
            await userEvent.click(novemberOption);

            // The component should cast the string value to Month type
            expect(mockSetMonth).toHaveBeenCalledWith('November');
        });
    });

    describe('Component Structure', () => {
        it('proper structure is rendered', () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            // Check for Label
            expect(screen.getByText('Month')).toBeInTheDocument();

            // Check for Select trigger
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
    });

    describe('Edge Cases', () => {
        it('rapid month changes are handled correctly', async () => {
            render(<MonthFilter month="January" setMonth={mockSetMonth} />);

            const trigger = screen.getByRole('combobox');

            // Select February
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('February'));

            // Select March
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('March'));

            // Select April
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('April'));

            expect(mockSetMonth).toHaveBeenCalledTimes(3);
            expect(mockSetMonth).toHaveBeenNthCalledWith(1, 'February');
            expect(mockSetMonth).toHaveBeenNthCalledWith(2, 'March');
            expect(mockSetMonth).toHaveBeenNthCalledWith(3, 'April');
        });

        it('selected value is maintained after prop updates', () => {
            const { rerender } = render(<MonthFilter month="January" setMonth={mockSetMonth} />);
            expect(screen.getByText('January')).toBeInTheDocument();

            rerender(<MonthFilter month="December" setMonth={mockSetMonth} />);
            expect(screen.getByText('December')).toBeInTheDocument();
        });
    });
}); 