import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockLineItem, render, screen } from '../../utils/test-utils';
import LineItem from '../LineItem';

describe('LineItem', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Rendering', () => {
        it('line item data is displayed correctly', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
            );

            expect(screen.getByText('Test transaction')).toBeInTheDocument();
            expect(screen.getByText('Test Store')).toBeInTheDocument();
            expect(screen.getByText('credit_card')).toBeInTheDocument();
            expect(screen.getByText('$50.00')).toBeInTheDocument();
        });

        it('checkbox is rendered when showCheckBox is true', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeInTheDocument();
        });

        it('checkbox is not rendered when showCheckBox is false', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={false} /></tbody></table>
            );

            const checkbox = screen.queryByRole('checkbox');
            expect(checkbox).not.toBeInTheDocument();
        });

        it('checkbox is not rendered when showCheckBox is not provided', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
            );

            const checkbox = screen.queryByRole('checkbox');
            expect(checkbox).not.toBeInTheDocument();
        });

        it('date is formatted correctly', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
            );

            // The mock date is 1640995200 which should format to Jan 1, 2022
            expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
        });

        it('table cells are rendered in correct order', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const cells = screen.getAllByRole('cell');
            expect(cells).toHaveLength(6); // checkbox + 5 data cells
            expect(cells[1]).toHaveTextContent('Jan 1, 2022');
            expect(cells[2]).toHaveTextContent('credit_card');
            expect(cells[3]).toHaveTextContent('Test transaction');
            expect(cells[4]).toHaveTextContent('Test Store');
            expect(cells[5]).toHaveTextContent('$50.00');
        });

        it('table cells are rendered without checkbox column when showCheckBox is false', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={false} /></tbody></table>
            );

            const cells = screen.getAllByRole('cell');
            expect(cells).toHaveLength(5); // 5 data cells only
            expect(cells[0]).toHaveTextContent('Jan 1, 2022');
            expect(cells[1]).toHaveTextContent('credit_card');
            expect(cells[2]).toHaveTextContent('Test transaction');
            expect(cells[3]).toHaveTextContent('Test Store');
            expect(cells[4]).toHaveTextContent('$50.00');
        });
    });

    describe('Checkbox State Management', () => {
        it('checkbox is checked when isChecked is true', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} isChecked={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeChecked();
        });

        it('checkbox is unchecked when isChecked is false', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} isChecked={false} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();
        });

        it('checkbox is unchecked by default when isChecked is not provided', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();
        });
    });

    describe('User Interactions', () => {
        it('onToggle is called with line item id when checkbox is clicked', async () => {
            const mockToggle = jest.fn();
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} onToggle={mockToggle} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);

            expect(mockToggle).toHaveBeenCalledTimes(1);
            expect(mockToggle).toHaveBeenCalledWith(mockLineItem.id);
        });

        it('multiple checkbox clicks call onToggle multiple times', async () => {
            const mockToggle = jest.fn();
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} onToggle={mockToggle} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);
            await userEvent.click(checkbox);

            expect(mockToggle).toHaveBeenCalledTimes(2);
        });

        it('focus is maintained after checkbox interaction', async () => {
            const mockToggle = jest.fn();
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} onToggle={mockToggle} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);
            expect(checkbox).toHaveFocus();
        });
    });

    describe('Date Formatting', () => {
        it('different dates are formatted correctly', () => {
            const testCases = [
                { date: 1640995200, expected: 'Jan 1, 2022' }, // 2022-01-01
                { date: 1672531200, expected: 'Jan 1, 2023' }, // 2023-01-01
                { date: 1704067200, expected: 'Jan 1, 2024' }, // 2024-01-01
                { date: 1640995200 + 86400, expected: 'Jan 2, 2022' }, // 2022-01-02
            ];

            testCases.forEach(({ date, expected }) => {
                const lineItemWithDate = { ...mockLineItem, date };
                render(
                    <table><tbody><LineItem lineItem={lineItemWithDate} /></tbody></table>
                );
                expect(screen.getByText(expected)).toBeInTheDocument();
            });
        });

        it('edge case dates are handled correctly', () => {
            // Test end of year
            const endOfYearLineItem = { ...mockLineItem, date: 1672531199 }; // 2022-12-31 23:59:59
            render(
                <table><tbody><LineItem lineItem={endOfYearLineItem} /></tbody></table>
            );
            expect(screen.getByText('Dec 31, 2022')).toBeInTheDocument();
        });
    });

    describe('Props Handling', () => {
        it('different line item data types are handled correctly', () => {
            const testLineItem = {
                _id: 'test-id',
                id: 'test-id',
                date: 1640995200,
                payment_method: 'cash',
                description: 'Cash transaction',
                responsible_party: 'Local Store',
                amount: 25.50,
                isSelected: false,
            };

            render(
                <table><tbody><LineItem lineItem={testLineItem} /></tbody></table>
            );

            expect(screen.getByText('Cash transaction')).toBeInTheDocument();
            expect(screen.getByText('Local Store')).toBeInTheDocument();
            expect(screen.getByText('cash')).toBeInTheDocument();
            expect(screen.getByText('$25.50')).toBeInTheDocument();
        });

        it('zero amount is displayed correctly', () => {
            const zeroAmountLineItem = { ...mockLineItem, amount: 0 };
            render(
                <table><tbody><LineItem lineItem={zeroAmountLineItem} /></tbody></table>
            );

            expect(screen.getByText('$0.00')).toBeInTheDocument();
        });

        it('large amounts are displayed correctly', () => {
            const largeAmountLineItem = { ...mockLineItem, amount: 999999.99 };
            render(
                <table><tbody><LineItem lineItem={largeAmountLineItem} /></tbody></table>
            );

            expect(screen.getByText('$999,999.99')).toBeInTheDocument();
        });

        it('empty strings in text fields are handled correctly', () => {
            const emptyFieldsLineItem = {
                ...mockLineItem,
                description: '',
                responsible_party: '',
            };
            render(
                <table><tbody><LineItem lineItem={emptyFieldsLineItem} /></tbody></table>
            );

            // Should render empty cells without errors
            const cells = screen.getAllByRole('cell');
            expect(cells).toHaveLength(5);
        });
    });

    describe('Accessibility', () => {
        it('table structure is proper', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const row = screen.getByRole('row');
            expect(row).toBeInTheDocument();
        });

        it('checkbox has proper accessibility attributes', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeInTheDocument();
            expect(checkbox).toHaveAttribute('role', 'checkbox');
        });

        it('table cell structure is maintained', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const cells = screen.getAllByRole('cell');
            expect(cells.length).toBeGreaterThan(0);
            cells.forEach(cell => {
                expect(cell.tagName).toBe('TD');
            });
        });
    });

    describe('Edge Cases', () => {
        it('checkbox defaults to unchecked when isChecked is not provided', () => {
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();
        });

        it('line item with missing properties is handled correctly', () => {
            const incompleteLineItem = {
                _id: 'incomplete',
                id: 'incomplete',
                date: 1640995200,
                // Missing other properties
            } as any;

            render(
                <table><tbody><LineItem lineItem={incompleteLineItem} /></tbody></table>
            );

            // Should render without crashing
            expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
        });

        it('rapid checkbox interactions are handled correctly', async () => {
            const mockToggle = jest.fn();
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} onToggle={mockToggle} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');

            // Rapid clicks
            await userEvent.click(checkbox);
            await userEvent.click(checkbox);
            await userEvent.click(checkbox);

            expect(mockToggle).toHaveBeenCalledTimes(3);
        });

        it('selection state updates when isChecked prop changes', () => {
            const { rerender } = render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} isChecked={false} /></tbody></table>
            );

            let checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();

            rerender(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} isChecked={true} /></tbody></table>
            );

            checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeChecked();
        });
    });
});
