import { act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import { LineItemInterface, LineItemsProvider, useLineItems, useLineItemsDispatch } from '../LineItemsContext';
import { AuthProvider } from '../AuthContext';

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

// Test component to use the context
const TestComponent = () => {
    const lineItems = useLineItems();
    const dispatch = useLineItemsDispatch();

    const handleToggle = () => {
        dispatch({
            type: 'toggle_line_item_select',
            lineItemId: '1'
        });
    };

    const handleRemove = () => {
        dispatch({
            type: 'remove_line_items',
            lineItemIds: ['1', '2']
        });
    };

    return (
        <div>
            <div data-testid="line-items-count">{lineItems.length}</div>
            <div data-testid="line-items-list">
                {lineItems.map(item => (
                    <div key={item.id} data-testid={`line-item-${item.id}`}>
                        {item.description} - {item.isSelected ? 'selected' : 'not selected'}
                    </div>
                ))}
            </div>
            <button onClick={handleToggle} data-testid="toggle-button">Toggle Item 1</button>
            <button onClick={handleRemove} data-testid="remove-button">Remove Items</button>
        </div>
    );
};

const mockLineItems: LineItemInterface[] = [
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
    }
];

// Helper wrapper that provides both Auth and LineItems contexts
const renderWithProviders = (ui: React.ReactElement) => {
    return render(
        <AuthProvider>
            {ui}
        </AuthProvider>
    );
};

describe('LineItemsContext', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Mock authenticated user for auth check, and line items for the actual data
        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url.includes('api/auth/me')) {
                return Promise.resolve({
                    data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                });
            }
            return Promise.resolve({ data: { data: mockLineItems } });
        });
    });

    describe('Provider Initialization', () => {
        it('renders children correctly', () => {
            renderWithProviders(
                <LineItemsProvider>
                    <div data-testid="child">Child Component</div>
                </LineItemsProvider>
            );

            expect(screen.getByTestId('child')).toBeInTheDocument();
        });

        it('fetches line items on mount', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/line_items'),
                    expect.objectContaining({
                        params: {
                            only_line_items_to_review: true
                        }
                    })
                );
            });
        });

        it('populates line items after successful API call', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('2');
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - not selected');
                expect(screen.getByTestId('line-item-2')).toHaveTextContent('Test transaction 2 - not selected');
            });
        });
    });

    describe('Context Hooks', () => {
        it('provides line items through useLineItems hook', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('2');
            });
        });

        it('provides dispatch function through useLineItemsDispatch hook', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('toggle-button')).toBeInTheDocument();
                expect(screen.getByTestId('remove-button')).toBeInTheDocument();
            });
        });
    });

    describe('Reducer Actions', () => {
        it('handles toggle_line_item_select action', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - not selected');
            });

            const toggleButton = screen.getByTestId('toggle-button');
            await act(async () => {
                await userEvent.click(toggleButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - selected');
            });
        });

        it('handles remove_line_items action', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('2');
            });

            const removeButton = screen.getByTestId('remove-button');
            await act(async () => {
                await userEvent.click(removeButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('0');
            });
        });

        it('handles populate_line_items action', async () => {
            const newLineItems = [
                {
                    _id: '3',
                    id: '3',
                    date: 1640995200,
                    payment_method: 'debit_card',
                    description: 'New transaction',
                    responsible_party: 'New Store',
                    amount: 75.00,
                    isSelected: false,
                }
            ];

            // First call is for auth, second for line items
            mockAxiosInstance.get
                .mockResolvedValueOnce({ data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' } })
                .mockResolvedValueOnce({ data: { data: newLineItems } });

            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('1');
                expect(screen.getByTestId('line-item-3')).toHaveTextContent('New transaction - not selected');
            });
        });
    });

    describe('Error Handling', () => {
        it('handles API error gracefully', async () => {
            const { toast } = require('sonner');
            // Auth succeeds, but line items fails
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('api/auth/me')) {
                    return Promise.resolve({
                        data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                    });
                }
                return Promise.reject(new Error('API Error'));
            });

            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith("Error", {
                    description: "API Error",
                    duration: 3500,
                });
            });
        });

        it('maintains empty state when API fails', async () => {
            // Auth succeeds, but line items fails
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('api/auth/me')) {
                    return Promise.resolve({
                        data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                    });
                }
                return Promise.reject(new Error('API Error'));
            });

            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('0');
            });
        });
    });

    describe('State Management', () => {
        it('maintains state across multiple actions', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('2');
            });

            // Toggle first item
            const toggleButton = screen.getByTestId('toggle-button');
            await act(async () => {
                await userEvent.click(toggleButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - selected');
            }, { timeout: 3000 });

            // Remove items
            const removeButton = screen.getByTestId('remove-button');
            await act(async () => {
                await userEvent.click(removeButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('0');
            });
        });

        it('handles multiple toggle operations', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - not selected');
            });

            const toggleButton = screen.getByTestId('toggle-button');

            // Toggle on
            await act(async () => {
                await userEvent.click(toggleButton);
            });
            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - selected');
            });

            // Toggle off
            await act(async () => {
                await userEvent.click(toggleButton);
            });
            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - not selected');
            });
        });
    });

    describe('API Integration', () => {
        it('uses correct API endpoint', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/line_items'),
                    expect.objectContaining({
                        params: {
                            only_line_items_to_review: true
                        }
                    })
                );
            });
        });

        it('handles different API response structures', async () => {
            const differentLineItems = [
                {
                    _id: '4',
                    id: '4',
                    date: 1640995200,
                    payment_method: 'paypal',
                    description: 'Different transaction',
                    responsible_party: 'Different Store',
                    amount: 25.00,
                    isSelected: true,
                }
            ];

            // Override the mock to return different line items
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('api/auth/me')) {
                    return Promise.resolve({
                        data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                    });
                }
                return Promise.resolve({ data: { data: differentLineItems } });
            });

            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('1');
                expect(screen.getByTestId('line-item-4')).toHaveTextContent('Different transaction - selected');
            });
        });
    });
}); 