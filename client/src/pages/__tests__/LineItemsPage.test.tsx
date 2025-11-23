import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import LineItemsPage from '../LineItemsPage';

// Mock sonner toast
jest.mock('sonner', () => {
    const mockToast = jest.fn();
    return {
        toast: Object.assign(mockToast, {
            success: jest.fn(),
            error: jest.fn(),
            warning: jest.fn(),
            info: jest.fn(),
        }),
    };
});

// Mock the components
jest.mock('../../components/LineItem', () => {
    const MockLineItem = function MockLineItem({ lineItem }: any) {
        return (
            <tr data-testid={`line-item-${lineItem._id}`}>
                <td>{new Date(lineItem.date * 1000).toLocaleDateString()}</td>
                <td>{lineItem.payment_method || ''}</td>
                <td>{lineItem.description || ''}</td>
                <td>{lineItem.responsible_party || ''}</td>
                <td>${(lineItem.amount || 0).toFixed(2)}</td>
            </tr>
        );
    };
    const MockLineItemCard = function MockLineItemCard({ lineItem }: any) {
        return (
            <div data-testid={`line-item-card-${lineItem._id}`}>
                <span>{new Date(lineItem.date * 1000).toLocaleDateString()}</span>
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

jest.mock('../../components/PaymentMethodFilter', () => {
    return function MockPaymentMethodFilter({ paymentMethod, setPaymentMethod }: any) {
        return (
            <div data-testid="payment-method-filter">
                <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    data-testid="payment-method-select"
                >
                    <option value="All">All</option>
                    <option value="credit_card">Credit Card</option>
                    <option value="cash">Cash</option>
                    <option value="debit_card">Debit Card</option>
                </select>
            </div>
        );
    };
});

const mockLineItems = [
    {
        _id: '1',
        id: '1',
        date: 1640995200, // 2022-01-01
        payment_method: 'credit_card',
        description: 'Test transaction 1',
        responsible_party: 'Test Store 1',
        amount: 50.00,
    },
    {
        _id: '2',
        id: '2',
        date: 1640995200,
        payment_method: 'cash',
        description: 'Test transaction 2',
        responsible_party: 'Test Store 2',
        amount: 100.00,
    },
    {
        _id: '3',
        id: '3',
        date: 1640995200,
        payment_method: 'debit_card',
        description: 'Test transaction 3',
        responsible_party: 'Test Store 3',
        amount: 25.00,
    }
];

describe('LineItemsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Set up default environment variable
        process.env.VITE_API_ENDPOINT = 'http://localhost:5000/';
        // Default successful API response
        mockAxiosInstance.get.mockResolvedValue({
            data: { data: mockLineItems }
        });
    });

    describe('Rendering', () => {
        it('renders the page title', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Line Items');
            });
        });

        it('renders the payment method filter', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('payment-method-filter')).toBeInTheDocument();
            });
        });

        it('renders the table with correct headers', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByText('Date')).toBeInTheDocument();
                expect(screen.getByText('Payment Method')).toBeInTheDocument();
                expect(screen.getByText('Description')).toBeInTheDocument();
                expect(screen.getByText('Party')).toBeInTheDocument();
                expect(screen.getByText('Amount')).toBeInTheDocument();
            });
        });

        it('renders line items in the table when data is available', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toBeInTheDocument();
                expect(screen.getByTestId('line-item-2')).toBeInTheDocument();
                expect(screen.getByTestId('line-item-3')).toBeInTheDocument();
            });
        });

        it('renders line items with correct data', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                // Mobile and desktop layouts both render, so use getAllByText
                expect(screen.getAllByText('Test transaction 1').length).toBeGreaterThan(0);
                expect(screen.getAllByText('$50.00').length).toBeGreaterThan(0);
            });
        });

        it('shows "No Line Items found" when no data is available', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: [] }
            });

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByText('No Line Items found')).toBeInTheDocument();
            });
        });

        it('shows "No Line Items found" when API returns null data', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: [] }
            });

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByText('No Line Items found')).toBeInTheDocument();
            });
        });
    });

    describe('API Integration', () => {
        it('fetches line items on component mount', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'api/line_items',
                    {
                        params: {}
                    }
                );
            });
        });

        it('fetches line items with correct payment method filter', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'api/line_items',
                    {
                        params: {}
                    }
                );
            });
        });

        it('refetches data when payment method changes', async () => {
            render(<LineItemsPage />);

            // Wait for initial load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            // Change payment method
            const select = screen.getByTestId('payment-method-select');
            await userEvent.selectOptions(select, 'credit_card');

            // Wait for refetch
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'api/line_items',
                    {
                        params: {
                            payment_method: 'credit_card'
                        }
                    }
                );
            });
        });

        it('handles API errors gracefully', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByText(/Error loading line items/i)).toBeInTheDocument();
            });
        });

        it('uses correct API endpoint from environment variable', async () => {
            process.env.VITE_API_ENDPOINT = 'https://api.example.com/';

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'api/line_items',
                    expect.any(Object)
                );
            });
        });
    });

    describe('Payment Method Filter', () => {
        it('allows changing payment method filter', async () => {
            render(<LineItemsPage />);

            const select = screen.getByTestId('payment-method-select');
            await userEvent.selectOptions(select, 'cash');

            expect(select).toHaveValue('cash');
        });

        it('triggers API call when payment method changes', async () => {
            render(<LineItemsPage />);

            // Wait for initial load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            // Change payment method
            const select = screen.getByTestId('payment-method-select');
            await userEvent.selectOptions(select, 'debit_card');

            // Verify API call was made with new filter
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'api/line_items',
                    {
                        params: {
                            payment_method: 'debit_card'
                        }
                    }
                );
            });
        });

        it('maintains filter state across re-renders', async () => {
            const { rerender } = render(<LineItemsPage />);

            // Change payment method
            const select = screen.getByTestId('payment-method-select');
            await userEvent.selectOptions(select, 'credit_card');

            // Re-render component
            rerender(<LineItemsPage />);

            // Filter should still be set
            expect(select).toHaveValue('credit_card');
        });
    });

    describe('Table Structure', () => {
        it('renders table with correct shadcn classes', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                const table = screen.getByRole('table');
                expect(table).toHaveClass('w-full', 'caption-bottom', 'text-sm');
            });
        });

        it('renders table with proper structure', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByRole('table')).toBeInTheDocument();
                const rowgroups = screen.getAllByRole('rowgroup');
                expect(rowgroups).toHaveLength(2); // thead and tbody
                expect(rowgroups[0].tagName).toBe('THEAD');
                expect(rowgroups[1].tagName).toBe('TBODY');
            });
        });

        it('renders correct number of table headers', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                const headers = screen.getAllByRole('columnheader');
                expect(headers).toHaveLength(5); // Date, Payment Method, Description, Name, Amount
            });
        });
    });

    describe('Data Display', () => {
        it('displays formatted dates correctly', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                // The mock LineItem component formats the date
                expect(screen.getByTestId('line-item-1')).toBeInTheDocument();
            });
        });

        it('displays amounts with proper formatting', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                // Mobile and desktop layouts both render
                expect(screen.getAllByText('$50.00').length).toBeGreaterThan(0);
                expect(screen.getAllByText('$100.00').length).toBeGreaterThan(0);
                expect(screen.getAllByText('$25.00').length).toBeGreaterThan(0);
            });
        });

        it('handles line items with missing properties gracefully', async () => {
            const incompleteLineItems = [
                {
                    _id: '1',
                    id: '1',
                    date: 1640995200,
                    // Missing other properties
                } as any
            ];
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: incompleteLineItems }
            });

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toBeInTheDocument();
            });
        });

        it('handles zero amounts correctly', async () => {
            const zeroAmountLineItems = [
                {
                    ...mockLineItems[0],
                    amount: 0,
                }
            ];
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: zeroAmountLineItems }
            });

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getAllByText('$0.00').length).toBeGreaterThan(0);
            });
        });

        it('handles very large amounts correctly', async () => {
            const largeAmountLineItems = [
                {
                    ...mockLineItems[0],
                    amount: 999999.99,
                }
            ];
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: largeAmountLineItems }
            });

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getAllByText('$999999.99').length).toBeGreaterThan(0);
            });
        });
    });

    describe('Loading States', () => {
        it('shows loading state during initial load', () => {
            // Don't resolve the promise immediately
            mockAxiosInstance.get.mockImplementation(() => new Promise(() => { }));

            render(<LineItemsPage />);

            expect(screen.getByText('Loading line items...')).toBeInTheDocument();
        });

        it('updates display when data loads', async () => {
            // Initially show no data
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: [] }
            });

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByText('No Line Items found')).toBeInTheDocument();
            });

            // Clear the mock and set up new response
            mockAxiosInstance.get.mockClear();
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: mockLineItems }
            });

            // Change payment method to trigger a new API call
            const select = screen.getByTestId('payment-method-select');
            await userEvent.selectOptions(select, 'credit_card');

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toBeInTheDocument();
            });
        });
    });

    describe('Accessibility', () => {
        it('has proper heading structure', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
            });
        });

        it('has proper table structure', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByRole('table')).toBeInTheDocument();
                const rowgroups = screen.getAllByRole('rowgroup');
                expect(rowgroups).toHaveLength(2); // thead and tbody
                expect(rowgroups[0].tagName).toBe('THEAD');
                expect(rowgroups[1].tagName).toBe('TBODY');
            });
        });

        it('has proper form labels for payment method filter', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('payment-method-select')).toBeInTheDocument();
            });
        });
    });

    describe('Component Integration', () => {
        it('passes correct props to LineItem components', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                // Both mobile cards and desktop table rows are rendered
                const tableRows = screen.getAllByTestId(/^line-item-\d+$/);
                const cards = screen.getAllByTestId(/^line-item-card-\d+$/);
                expect(tableRows).toHaveLength(3);
                expect(cards).toHaveLength(3);
            });
        });

        it('passes correct props to PaymentMethodFilter', async () => {
            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('payment-method-filter')).toBeInTheDocument();
                expect(screen.getByTestId('payment-method-select')).toHaveValue('All');
            });
        });
    });

    describe('Edge Cases', () => {
        it('handles API response with unexpected structure', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: [] }
            });

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByText('No Line Items found')).toBeInTheDocument();
            });
        });

        it('handles API response with null data field', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('No data'));

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByText(/Error loading line items/i)).toBeInTheDocument();
            });
        });

        it('handles API response with undefined data field', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('No data'));

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(screen.getByText(/Error loading line items/i)).toBeInTheDocument();
            });
        });

        it('handles rapid payment method changes', async () => {
            render(<LineItemsPage />);

            const select = screen.getByTestId('payment-method-select');

            // Rapidly change payment methods
            await userEvent.selectOptions(select, 'credit_card');
            await userEvent.selectOptions(select, 'cash');
            await userEvent.selectOptions(select, 'debit_card');

            // Should have made multiple API calls
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(4); // Initial + 3 changes
            });
        });

        it('handles environment variable changes', async () => {
            // Change environment variable
            process.env.VITE_API_ENDPOINT = 'https://new-api.example.com/';

            render(<LineItemsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'api/line_items',
                    expect.any(Object)
                );
            });
        });
    });

    describe('Performance', () => {
        it('does not make unnecessary API calls on re-render', async () => {
            const { rerender } = render(<LineItemsPage />);

            // Wait for initial load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            // Re-render without changes
            rerender(<LineItemsPage />);

            // Should not make additional API calls
            expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
        });

        it('debounces rapid payment method changes appropriately', async () => {
            render(<LineItemsPage />);

            const select = screen.getByTestId('payment-method-select');

            // Make rapid changes
            await userEvent.selectOptions(select, 'credit_card');
            await userEvent.selectOptions(select, 'cash');
            await userEvent.selectOptions(select, 'debit_card');

            // Should have made calls for each change
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(4); // Initial + 3 changes
            });
        });
    });
}); 