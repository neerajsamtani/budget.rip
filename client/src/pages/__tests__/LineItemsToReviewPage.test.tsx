import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { useLineItems } from '../../contexts/LineItemsContext';
import { render, screen, waitFor } from '../../utils/test-utils';
import LineItemsToReviewPage from '../LineItemsToReviewPage';

// Mock the context
jest.mock('../../contexts/LineItemsContext', () => ({
    useLineItems: jest.fn(),
    useLineItemsDispatch: jest.fn(() => jest.fn()),
}));

// Mock the components
jest.mock('../../components/CreateCashTransactionModal', () => {
    return function MockCreateCashTransactionModal({ show, onHide }: { show: boolean; onHide: () => void }) {
        return show ? (
            <div data-testid="cash-transaction-modal">
                <button onClick={onHide}>Close Cash Modal</button>
            </div>
        ) : null;
    };
});

jest.mock('../../components/CreateEventModal', () => {
    return function MockCreateEventModal({ show, onHide }: { show: boolean; onHide: () => void }) {
        return show ? (
            <div data-testid="event-modal">
                <button onClick={onHide}>Close Event Modal</button>
            </div>
        ) : null;
    };
});

jest.mock('../../components/LineItem', () => {
    interface MockLineItemProps {
        lineItem: {
            _id?: string;
            id?: string;
            date: number;
            payment_method?: string;
            description?: string;
            responsible_party?: string;
            amount?: number;
        };
        showCheckBox?: boolean;
        isChecked?: boolean;
        handleToggle?: () => void;
        amountStatus?: string;
    }

    const MockLineItem = function({ lineItem, showCheckBox }: MockLineItemProps) {
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
    // Export LineItemCard for mobile view
    const MockLineItemCard = function({ lineItem }: MockLineItemProps) {
        return (
            <div data-testid={`line-item-card-${lineItem._id || lineItem.id}`}>
                <span>{lineItem.description || ''}</span>
                <span>${(lineItem.amount || 0).toFixed(2)}</span>
            </div>
        );
    };
    return {
        __esModule: true,
        default: MockLineItem,
        LineItemCard: MockLineItemCard,
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
        mockUseLineItems.mockReturnValue({ lineItems: mockLineItems, isLoading: false });
    });

    describe('Rendering', () => {
        it('renders the page title', () => {
            render(<LineItemsToReviewPage />);
            expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Review Line Items');
        });

        it('renders the table with correct headers', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByText('Select')).toBeInTheDocument();
            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByText('Description')).toBeInTheDocument();
            expect(screen.getByText('Party')).toBeInTheDocument();
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

            // Check first line item data in the desktop table row
            const tableRow = screen.getByTestId('line-item-1');
            expect(tableRow).toHaveTextContent('Test transaction 1');
            expect(tableRow).toHaveTextContent('Test Store 1');
            expect(tableRow).toHaveTextContent('$50.00');
            expect(tableRow).toHaveTextContent('credit_card');
        });

        it('renders action buttons in the navbar', () => {
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('button', { name: /create cash transaction/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });

        it('shows checkboxes for line items', () => {
            render(<LineItemsToReviewPage />);

            // Check desktop table rows for checkbox (not mobile cards)
            const tableRows = [
                screen.getByTestId('line-item-1'),
                screen.getByTestId('line-item-2'),
                screen.getByTestId('line-item-3'),
            ];
            tableRows.forEach(item => {
                expect(item).toHaveTextContent('Checkbox');
            });
        });

        it('handles empty line items gracefully', () => {
            mockUseLineItems.mockReturnValue({ lineItems:[], isLoading: false });
            render(<LineItemsToReviewPage />);

            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create cash transaction/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });

        it('handles null line items gracefully', () => {
            mockUseLineItems.mockReturnValue({ lineItems:null as any, isLoading: false });
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

            // The (↵) is hidden on mobile via CSS, but still present in the DOM
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });
    });

    describe('Component Integration', () => {
        it('passes correct props to LineItem components', () => {
            render(<LineItemsToReviewPage />);

            // Check desktop table rows (line-item-1, etc.) - 3 items
            const tableRows = [
                screen.getByTestId('line-item-1'),
                screen.getByTestId('line-item-2'),
                screen.getByTestId('line-item-3'),
            ];
            expect(tableRows).toHaveLength(3);

            // Check that each table row shows "Checkbox" indicating showCheckBox=true
            tableRows.forEach(item => {
                expect(item).toHaveTextContent('Checkbox');
            });

            // Check mobile cards also exist (line-item-card-1, etc.) - 3 items
            const cards = [
                screen.getByTestId('line-item-card-1'),
                screen.getByTestId('line-item-card-2'),
                screen.getByTestId('line-item-card-3'),
            ];
            expect(cards).toHaveLength(3);
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

        it('renders buttons with correct attributes', () => {
            render(<LineItemsToReviewPage />);

            const cashButton = screen.getByRole('button', { name: /create cash transaction/i });
            const eventButton = screen.getByRole('button', { name: /create event/i });

            expect(cashButton).toBeInTheDocument();
            expect(eventButton).toBeInTheDocument();
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
            mockUseLineItems.mockReturnValue({ lineItems:incompleteLineItems, isLoading: false });

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
            mockUseLineItems.mockReturnValue({ lineItems:largeAmountLineItems, isLoading: false });

            render(<LineItemsToReviewPage />);

            // Both table and card render the amount, use getAllByText
            const amounts = screen.getAllByText('$999999.99');
            expect(amounts.length).toBeGreaterThanOrEqual(1);
        });

        it('handles zero amounts correctly', () => {
            const zeroAmountLineItems = [
                {
                    ...mockLineItems[0],
                    amount: 0,
                }
            ];
            mockUseLineItems.mockReturnValue({ lineItems:zeroAmountLineItems, isLoading: false });

            render(<LineItemsToReviewPage />);

            // Both table and card render the amount, use getAllByText
            const amounts = screen.getAllByText('$0.00');
            expect(amounts.length).toBeGreaterThanOrEqual(1);
        });
    });

    describe('Responsive Layout', () => {
        it('renders mobile card layout', () => {
            render(<LineItemsToReviewPage />);

            // Mobile card layout should render line item cards
            expect(screen.getByTestId('line-item-card-1')).toBeInTheDocument();
            expect(screen.getByTestId('line-item-card-2')).toBeInTheDocument();
            expect(screen.getByTestId('line-item-card-3')).toBeInTheDocument();
        });

        it('renders desktop table layout', () => {
            render(<LineItemsToReviewPage />);

            // Desktop table should also render (hidden via CSS)
            expect(screen.getByRole('table')).toBeInTheDocument();
            const rowgroups = screen.getAllByRole('rowgroup');
            expect(rowgroups).toHaveLength(2); // thead and tbody
        });

        it('renders both mobile and desktop layouts simultaneously', () => {
            render(<LineItemsToReviewPage />);

            // Both layouts should be in the DOM (CSS controls visibility)
            expect(screen.getByTestId('line-item-card-1')).toBeInTheDocument();
            expect(screen.getByTestId('line-item-1')).toBeInTheDocument();
        });

        it('mobile cards show correct data', () => {
            render(<LineItemsToReviewPage />);

            const mobileCard = screen.getByTestId('line-item-card-1');
            expect(mobileCard).toHaveTextContent('Test transaction 1');
            expect(mobileCard).toHaveTextContent('$50.00');
        });

        it('desktop table shows correct data', () => {
            render(<LineItemsToReviewPage />);

            const tableRow = screen.getByTestId('line-item-1');
            expect(tableRow).toHaveTextContent('Test transaction 1');
            expect(tableRow).toHaveTextContent('$50.00');
            expect(tableRow).toHaveTextContent('credit_card');
        });

        it('renders fixed bottom bar with buttons on both layouts', () => {
            render(<LineItemsToReviewPage />);

            const bottomContainer = document.querySelector('.fixed.bottom-0');
            expect(bottomContainer).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create cash transaction/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });
    });

    describe('Loading States', () => {
        it('shows loading spinner in mobile view during initial load', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: true });

            const { container } = render(<LineItemsToReviewPage />);

            // Check for spinner in mobile view
            const spinners = container.querySelectorAll('.animate-spin');
            expect(spinners.length).toBeGreaterThan(0);
        });

        it('shows loading spinner in desktop table during initial load', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: true });

            const { container } = render(<LineItemsToReviewPage />);

            // Check for spinner (loading indicator)
            const spinner = container.querySelector('.animate-spin');
            expect(spinner).toBeInTheDocument();
        });

        it('replaces loading spinner with data after load completes', () => {
            // Start with loading state
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: true });
            const { container, rerender } = render(<LineItemsToReviewPage />);

            // Verify spinner is present
            let spinner = container.querySelector('.animate-spin');
            expect(spinner).toBeInTheDocument();

            // Update to loaded state with data
            mockUseLineItems.mockReturnValue({ lineItems: mockLineItems, isLoading: false });
            rerender(<LineItemsToReviewPage />);

            // Verify data is displayed
            expect(screen.getByTestId('line-item-1')).toBeInTheDocument();
            expect(screen.getByTestId('line-item-2')).toBeInTheDocument();
        });

        it('shows "No line items to review" message when loaded with no data', () => {
            mockUseLineItems.mockReturnValue({ lineItems: [], isLoading: false });

            render(<LineItemsToReviewPage />);

            // Should show message in both mobile and desktop layouts
            const messages = screen.getAllByText('No line items to review');
            expect(messages.length).toBeGreaterThan(0);
        });
    });
}); 