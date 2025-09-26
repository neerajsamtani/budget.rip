import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { useLineItems } from '../../contexts/LineItemsContext';
import { render, screen, waitFor } from '../../utils/test-utils';
import LineItemsToReviewPage from '../LineItemsToReviewPage';

// Mock the context
jest.mock('../../contexts/LineItemsContext', () => ({
    useLineItems: jest.fn(),
}));

// Mock the components
jest.mock('../../components/CreateCashTransactionModal', () => {
    return function MockCreateCashTransactionModal({ show, onHide }: any) {
        return show ? (
            <div data-testid="cash-transaction-modal">
                <button onClick={onHide}>Close Cash Modal</button>
            </div>
        ) : null;
    };
});

jest.mock('../../components/CreateEventModal', () => {
    return function MockCreateEventModal({ show, onHide }: any) {
        return show ? (
            <div data-testid="event-modal">
                <button onClick={onHide}>Close Event Modal</button>
            </div>
        ) : null;
    };
});

jest.mock('../../components/LineItem', () => {
    return function MockLineItem({ lineItem, showCheckBox }: any) {
        return (
            <tr data-testid={`line-item-${lineItem._id}`}>
                <td>{showCheckBox ? 'Checkbox' : 'No Checkbox'}</td>
                <td>{new Date(lineItem.date * 1000).toLocaleDateString()}</td>
                <td>{lineItem.payment_method || ''}</td>
                <td>{lineItem.description || ''}</td>
                <td>{lineItem.responsible_party || ''}</td>
                <td>${(lineItem.amount || 0).toFixed(2)}</td>
            </tr>
        );
    };
});

const mockUseLineItems = useLineItems as jest.MockedFunction<typeof useLineItems>;

const mockLineItems = [
    {
        _id: '1',
        id: '1',
        date: 1640995200,
        payment_method: 'credit_card',
        description: 'Test transaction 1',
        responsible_party: 'Test Store 1',
        amount: 50.00,
        isSelected: false,
    },
    {
        _id: '2',
        id: '2',
        date: 1640995200,
        payment_method: 'cash',
        description: 'Test transaction 2',
        responsible_party: 'Test Store 2',
        amount: 100.00,
        isSelected: false,
    },
    {
        _id: '3',
        id: '3',
        date: 1640995200,
        payment_method: 'debit_card',
        description: 'Test transaction 3',
        responsible_party: 'Test Store 3',
        amount: 25.00,
        isSelected: false,
    }
];

describe('LineItemsToReviewPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockUseLineItems.mockReturnValue(mockLineItems);
    });

    describe('Rendering', () => {
        it('renders the page title', () => {
            render(<LineItemsToReviewPage />);
            expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Line Items To Review');
        });

        it('renders the table with correct headers', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByText('Select')).toBeInTheDocument();
            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByText('Description')).toBeInTheDocument();
            expect(screen.getByText('Name')).toBeInTheDocument();
            expect(screen.getByText('Amount')).toBeInTheDocument();
        });

        it('renders line items in the table', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByTestId('line-item-1')).toBeInTheDocument();
            expect(screen.getByTestId('line-item-2')).toBeInTheDocument();
            expect(screen.getByTestId('line-item-3')).toBeInTheDocument();
        });

        it('renders line items with correct data', () => {
            render(<LineItemsToReviewPage />);

            // Check first line item data
            expect(screen.getByText('Test transaction 1')).toBeInTheDocument();
            expect(screen.getByText('Test Store 1')).toBeInTheDocument();
            expect(screen.getByText('$50.00')).toBeInTheDocument();
            expect(screen.getByText('credit_card')).toBeInTheDocument();
        });

        it('renders action buttons in the navbar', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('button', { name: /create cash transaction/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });

        it('shows checkboxes for line items', () => {
            render(<LineItemsToReviewPage />);

            const lineItems = screen.getAllByTestId(/line-item-/);
            lineItems.forEach(item => {
                expect(item).toHaveTextContent('Checkbox');
            });
        });

        it('handles empty line items gracefully', () => {
            mockUseLineItems.mockReturnValue([]);
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create cash transaction/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });

        it('handles null line items gracefully', () => {
            mockUseLineItems.mockReturnValue(null as any);
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create cash transaction/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });
    });

    describe('Modal Management', () => {
        it('opens cash transaction modal when button is clicked', async () => {
            render(<LineItemsToReviewPage />);

            const cashButton = screen.getByRole('button', { name: /create cash transaction/i });
            await userEvent.click(cashButton);

            expect(screen.getByTestId('cash-transaction-modal')).toBeInTheDocument();
        });

        it('opens event modal when button is clicked', async () => {
            render(<LineItemsToReviewPage />);

            const eventButton = screen.getByRole('button', { name: /create event/i });
            await userEvent.click(eventButton);

            expect(screen.getByTestId('event-modal')).toBeInTheDocument();
        });

        it('closes cash transaction modal when onHide is called', async () => {
            render(<LineItemsToReviewPage />);

            // Open modal
            const cashButton = screen.getByRole('button', { name: /create cash transaction/i });
            await userEvent.click(cashButton);
            expect(screen.getByTestId('cash-transaction-modal')).toBeInTheDocument();

            // Close modal
            const closeButton = screen.getByRole('button', { name: /close cash modal/i });
            await userEvent.click(closeButton);

            expect(screen.queryByTestId('cash-transaction-modal')).not.toBeInTheDocument();
        });

        it('closes event modal when onHide is called', async () => {
            render(<LineItemsToReviewPage />);

            // Open modal
            const eventButton = screen.getByRole('button', { name: /create event/i });
            await userEvent.click(eventButton);
            expect(screen.getByTestId('event-modal')).toBeInTheDocument();

            // Close modal
            const closeButton = screen.getByRole('button', { name: /close event modal/i });
            await userEvent.click(closeButton);

            expect(screen.queryByTestId('event-modal')).not.toBeInTheDocument();
        });

        it('can have both modals open simultaneously', async () => {
            render(<LineItemsToReviewPage />);

            // Open both modals
            const cashButton = screen.getByRole('button', { name: /create cash transaction/i });
            const eventButton = screen.getByRole('button', { name: /create event/i });

            await userEvent.click(cashButton);
            await userEvent.click(eventButton);

            expect(screen.getByTestId('cash-transaction-modal')).toBeInTheDocument();
            expect(screen.getByTestId('event-modal')).toBeInTheDocument();
        });
    });

    describe('Keyboard Interactions', () => {
        it('opens event modal when Enter key is pressed', async () => {
            render(<LineItemsToReviewPage />);

            // Simulate Enter key press
            fireEvent.keyDown(document, { key: 'Enter' });

            await waitFor(() => {
                expect(screen.getByTestId('event-modal')).toBeInTheDocument();
            });
        });

        it('does not open event modal for other key presses', async () => {
            render(<LineItemsToReviewPage />);

            // Simulate other key presses
            fireEvent.keyDown(document, { key: 'Space' });
            fireEvent.keyDown(document, { key: 'Tab' });
            fireEvent.keyDown(document, { key: 'Escape' });

            expect(screen.queryByTestId('event-modal')).not.toBeInTheDocument();
        });

        it('can open event modal multiple times with Enter key', async () => {
            render(<LineItemsToReviewPage />);

            // First Enter press
            fireEvent.keyDown(document, { key: 'Enter' });
            await waitFor(() => {
                expect(screen.getByTestId('event-modal')).toBeInTheDocument();
            });

            // Close modal
            const closeButton = screen.getByRole('button', { name: /close event modal/i });
            await userEvent.click(closeButton);

            // Second Enter press
            fireEvent.keyDown(document, { key: 'Enter' });
            await waitFor(() => {
                expect(screen.getByTestId('event-modal')).toBeInTheDocument();
            });
        });
    });

    describe('Event Listener Management', () => {
        it('adds and removes event listeners correctly', () => {
            const addEventListenerSpy = jest.spyOn(document, 'addEventListener');
            const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener');

            const { unmount } = render(<LineItemsToReviewPage />);

            expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));

            unmount();

            expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));

            addEventListenerSpy.mockRestore();
            removeEventListenerSpy.mockRestore();
        });
    });

    describe('Accessibility', () => {
        it('has proper heading structure', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
        });

        it('has proper table structure', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('table')).toBeInTheDocument();
            const rowgroups = screen.getAllByRole('rowgroup');
            expect(rowgroups).toHaveLength(2); // thead and tbody
            expect(rowgroups[0].tagName).toBe('THEAD');
            expect(rowgroups[1].tagName).toBe('TBODY');
        });

        it('has proper button labels', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('button', { name: /create cash transaction/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });

        it('indicates keyboard shortcut in button text', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('button', { name: /create event \(↵\)/i })).toBeInTheDocument();
        });
    });

    describe('Component Integration', () => {
        it('passes correct props to LineItem components', () => {
            render(<LineItemsToReviewPage />);

            const lineItems = screen.getAllByTestId(/line-item-/);
            expect(lineItems).toHaveLength(3);

            // Check that each line item shows "Checkbox" indicating showCheckBox=true
            lineItems.forEach(item => {
                expect(item).toHaveTextContent('Checkbox');
            });
        });

        it('passes correct props to CreateCashTransactionModal', async () => {
            render(<LineItemsToReviewPage />);

            const cashButton = screen.getByRole('button', { name: /create cash transaction/i });
            await userEvent.click(cashButton);

            expect(screen.getByTestId('cash-transaction-modal')).toBeInTheDocument();
        });

        it('passes correct props to CreateEventModal', async () => {
            render(<LineItemsToReviewPage />);

            const eventButton = screen.getByRole('button', { name: /create event/i });
            await userEvent.click(eventButton);

            expect(screen.getByTestId('event-modal')).toBeInTheDocument();
        });
    });

    describe('Styling and Layout', () => {
        it('renders navbar with fixed-bottom class', () => {
            render(<LineItemsToReviewPage />);

            // Check for the fixed bottom container with buttons
            const bottomContainer = document.querySelector('.fixed.bottom-0');
            expect(bottomContainer).toBeInTheDocument();

            // Verify buttons are present in the fixed bottom area
            const cashButton = screen.getByRole('button', { name: /create cash transaction/i });
            const eventButton = screen.getByRole('button', { name: /create event/i });
            expect(cashButton).toBeInTheDocument();
            expect(eventButton).toBeInTheDocument();
        });

        it('renders table with correct shadcn classes', () => {
            render(<LineItemsToReviewPage />);

            const table = screen.getByRole('table');
            expect(table).toHaveClass('w-full', 'caption-bottom', 'text-sm');
            expect(table).toHaveAttribute('data-slot', 'table');
        });

        it('renders buttons with correct variants', () => {
            render(<LineItemsToReviewPage />);

            const cashButton = screen.getByRole('button', { name: /create cash transaction/i });
            const eventButton = screen.getByRole('button', { name: /create event/i });

            expect(cashButton).toHaveClass('bg-primary', 'text-primary-foreground');
            expect(eventButton).toHaveClass('bg-primary', 'text-primary-foreground');
            expect(cashButton).toHaveAttribute('data-slot', 'button');
            expect(eventButton).toHaveAttribute('data-slot', 'button');
        });
    });

    describe('Edge Cases', () => {
        it('handles line items with missing properties gracefully', () => {
            const incompleteLineItems = [
                {
                    _id: '1',
                    id: '1',
                    date: 1640995200,
                    // Missing other properties
                } as any
            ];
            mockUseLineItems.mockReturnValue(incompleteLineItems);

            render(<LineItemsToReviewPage />);

            expect(screen.getByTestId('line-item-1')).toBeInTheDocument();
        });

        it('handles very large amounts correctly', () => {
            const largeAmountLineItems = [
                {
                    ...mockLineItems[0],
                    amount: 999999.99,
                }
            ];
            mockUseLineItems.mockReturnValue(largeAmountLineItems);

            render(<LineItemsToReviewPage />);

            expect(screen.getByText('$999999.99')).toBeInTheDocument();
        });

        it('handles zero amounts correctly', () => {
            const zeroAmountLineItems = [
                {
                    ...mockLineItems[0],
                    amount: 0,
                }
            ];
            mockUseLineItems.mockReturnValue(zeroAmountLineItems);

            render(<LineItemsToReviewPage />);

            expect(screen.getByText('$0.00')).toBeInTheDocument();
        });
    });
}); 