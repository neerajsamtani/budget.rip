import userEvent from '@testing-library/user-event';
import React from 'react';
import { useLineItems, useLineItemsDispatch } from '../../contexts/LineItemsContext';
import { mockLineItem, render, screen } from '../../utils/test-utils';
import LineItem from '../LineItem';

// Mock the context hooks
jest.mock('../../contexts/LineItemsContext', () => ({
    useLineItems: jest.fn(),
    useLineItemsDispatch: jest.fn(),
}));

const mockUseLineItems = useLineItems as jest.MockedFunction<typeof useLineItems>;
const mockUseLineItemsDispatch = useLineItemsDispatch as jest.MockedFunction<typeof useLineItemsDispatch>;

const mockDispatch = jest.fn();

describe('LineItem', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockUseLineItemsDispatch.mockReturnValue(mockDispatch);
    });

    describe('Rendering', () => {
        it('renders line item data correctly', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
            );

            expect(screen.getByText('Test transaction')).toBeInTheDocument();
            expect(screen.getByText('Test Store')).toBeInTheDocument();
            expect(screen.getByText('credit_card')).toBeInTheDocument();
            expect(screen.getByText('$50.00')).toBeInTheDocument();
        });

        it('renders checkbox when showCheckBox is true', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeInTheDocument();
        });

        it('does not render checkbox when showCheckBox is false', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={false} /></tbody></table>
            );

            const checkbox = screen.queryByRole('checkbox');
            expect(checkbox).not.toBeInTheDocument();
        });

        it('does not render checkbox when showCheckBox is not provided', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
            );

            const checkbox = screen.queryByRole('checkbox');
            expect(checkbox).not.toBeInTheDocument();
        });

        it('formats date correctly', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
            );

            // The mock date is 1640995200 which should format to Jan 1, 2022
            expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
        });

        it('renders all table cells in correct order', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
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

        it('renders without checkbox when showCheckBox is false', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
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
        it('shows checkbox as checked when line item is selected', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [
                { ...mockLineItem, isSelected: true }
            ], isLoading: false });

            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeChecked();
        });

        it('shows checkbox as unchecked when line item is not selected', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [
                { ...mockLineItem, isSelected: false }
            ], isLoading: false });

            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();
        });

        it('shows checkbox as unchecked when line item is not in context', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();
        });

        it('handles multiple line items in context correctly', () => {
            const otherLineItem = { ...mockLineItem, _id: '2', id: '2', isSelected: true };
            mockUseLineItems.mockReturnValue({ lineItems: [
                { ...mockLineItem, isSelected: false },
                otherLineItem
            ], isLoading: false });

            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();
        });
    });

    describe('User Interactions', () => {
        it('calls dispatch with toggle action when checkbox is clicked', async () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);

            expect(mockDispatch).toHaveBeenCalledWith({
                type: 'toggle_line_item_select',
                lineItemId: '1'
            });
        });

        it('calls dispatch with correct lineItemId', async () => {
            const customLineItem = { ...mockLineItem, id: 'custom-id' };
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={customLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);

            expect(mockDispatch).toHaveBeenCalledWith({
                type: 'toggle_line_item_select',
                lineItemId: 'custom-id'
            });
        });

        it('handles multiple checkbox clicks', async () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);
            await userEvent.click(checkbox);

            expect(mockDispatch).toHaveBeenCalledTimes(2);
            expect(mockDispatch).toHaveBeenNthCalledWith(1, {
                type: 'toggle_line_item_select',
                lineItemId: '1'
            });
            expect(mockDispatch).toHaveBeenNthCalledWith(2, {
                type: 'toggle_line_item_select',
                lineItemId: '1'
            });
        });

        it('maintains focus after checkbox interaction', async () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);
            expect(checkbox).toHaveFocus();
        });
    });

    describe('Date Formatting', () => {
        it('formats different dates correctly', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

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

        it('handles edge case dates', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

            // Test end of year
            const endOfYearLineItem = { ...mockLineItem, date: 1672531199 }; // 2022-12-31 23:59:59
            render(
                <table><tbody><LineItem lineItem={endOfYearLineItem} /></tbody></table>
            );
            expect(screen.getByText('Dec 31, 2022')).toBeInTheDocument();
        });
    });

    describe('Props Handling', () => {
        it('handles different line item data types', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

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

        it('handles zero amount', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

            const zeroAmountLineItem = { ...mockLineItem, amount: 0 };
            render(
                <table><tbody><LineItem lineItem={zeroAmountLineItem} /></tbody></table>
            );

            expect(screen.getByText('$0.00')).toBeInTheDocument();
        });

        it('handles large amounts', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

            const largeAmountLineItem = { ...mockLineItem, amount: 999999.99 };
            render(
                <table><tbody><LineItem lineItem={largeAmountLineItem} /></tbody></table>
            );

            expect(screen.getByText('$999,999.99')).toBeInTheDocument();
        });

        it('handles empty strings in text fields', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

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
        it('has proper table structure', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const row = screen.getByRole('row');
            expect(row).toBeInTheDocument();
        });

        it('has proper checkbox accessibility', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeInTheDocument();
            expect(checkbox).toHaveAttribute('role', 'checkbox');
        });

        it('maintains proper table cell structure', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
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
        it('handles empty context array', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();
        });

        it('handles line item with missing properties', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

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

        it('handles rapid checkbox interactions', async () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');

            // Rapid clicks
            await userEvent.click(checkbox);
            await userEvent.click(checkbox);
            await userEvent.click(checkbox);

            expect(mockDispatch).toHaveBeenCalledTimes(3);
        });
    });

    describe('Context Integration', () => {
        it('uses context data correctly for selection state', () => {
            const selectedLineItem = { ...mockLineItem, isSelected: true };
            mockUseLineItems.mockReturnValue({ lineItems: [selectedLineItem], isLoading: false });

            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeChecked();
        });

        it('updates selection state when context changes', () => {
            // Initially not selected
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });
            const { rerender } = render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            let checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();

            // Update context to show as selected
            mockUseLineItems.mockReturnValue({ lineItems: [{ ...mockLineItem, isSelected: true }], isLoading: false });
            rerender(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            checkbox = screen.getByRole('checkbox');
            expect(checkbox).toBeChecked();
        });

        it('matches line item by id for selection state', () => {
            const differentIdLineItem = { ...mockLineItem, id: 'different-id' };
            mockUseLineItems.mockReturnValue({ lineItems: [differentIdLineItem], isLoading: false });

            render(
                <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
            );

            const checkbox = screen.getByRole('checkbox');
            expect(checkbox).not.toBeChecked();
        });
    });
}); 