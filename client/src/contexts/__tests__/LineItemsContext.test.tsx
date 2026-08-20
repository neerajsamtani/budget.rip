import { useQueryClient } from '@tanstack/react-query';
import { act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor, within } from '../../utils/test-utils';
import LineItemsToReviewPage from '../../pages/LineItemsToReviewPage';
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
    const { lineItems, isPending } = useLineItems();
    const dispatch = useLineItemsDispatch();
    const queryClient = useQueryClient();

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
            <div data-testid="is-loading">{isPending ? 'loading' : 'not loading'}</div>
            <div data-testid="line-items-list">
                {lineItems.map(item => (
                    <div key={item.id} data-testid={`line-item-${item.id}`}>
                        {item.description} - {item.isSelected ? 'selected' : 'not selected'}
                    </div>
                ))}
            </div>
            <button onClick={handleToggle} data-testid="toggle-button">Toggle Item 1</button>
            <button onClick={handleRemove} data-testid="remove-button">Remove Items</button>
            <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ['lineItems'] })}
                data-testid="refetch-button"
            >
                Refetch
            </button>
        </div>
    );
};

const mockLineItems: LineItemInterface[] = [
    {
        id: '1',
        date: 1640995200,
        payment_method: 'credit_card',
        description: 'Test transaction 1',
        responsible_party: 'Test Store 1',
        amount: 50.00,
        isSelected: false,
    },
    {
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
        it('children are rendered correctly', () => {
            renderWithProviders(
                <LineItemsProvider>
                    <div data-testid="child">Child Component</div>
                </LineItemsProvider>
            );

            expect(screen.getByTestId('child')).toBeInTheDocument();
        });

        it('line items are fetched on mount', async () => {
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

        it('line items are populated after successful API call', async () => {
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
        it('line items are provided through useLineItems hook', async () => {
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

        it('dispatch function is provided through useLineItemsDispatch hook', async () => {
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
        it('toggle_line_item_select action is handled', async () => {
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

        it('remove_line_items action is handled', async () => {
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

        it('toggle_line_item_select sets unselected item to selected, leaving other items unchanged', async () => {
            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - not selected');
                expect(screen.getByTestId('line-item-2')).toHaveTextContent('Test transaction 2 - not selected');
            });

            await act(async () => {
                await userEvent.click(screen.getByTestId('toggle-button'));
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - selected');
                expect(screen.getByTestId('line-item-2')).toHaveTextContent('Test transaction 2 - not selected');
            });
        });

        it('toggle_line_item_select sets selected item to unselected', async () => {
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('api/auth/me')) {
                    return Promise.resolve({
                        data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                    });
                }
                return Promise.resolve({ data: { data: [{ ...mockLineItems[0], isSelected: true }, mockLineItems[1]] } });
            });

            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <TestComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - selected');
            });

            await act(async () => {
                await userEvent.click(screen.getByTestId('toggle-button'));
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - not selected');
            });
        });

        it('remove_line_items removes only the specified items', async () => {
            const threeLineItems = [
                ...mockLineItems,
                {
                    id: '3',
                    date: 1640995200,
                    payment_method: 'debit_card',
                    description: 'Test transaction 3',
                    responsible_party: 'Test Store 3',
                    amount: 25.00,
                    isSelected: false,
                }
            ];

            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('api/auth/me')) {
                    return Promise.resolve({
                        data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                    });
                }
                return Promise.resolve({ data: { data: threeLineItems } });
            });

            const RemoveSpecificComponent = () => {
                const { lineItems } = useLineItems();
                const dispatch = useLineItemsDispatch();
                return (
                    <div>
                        <div data-testid="line-items-count">{lineItems.length}</div>
                        {lineItems.map(item => (
                            <div key={item.id} data-testid={`line-item-${item.id}`}>{item.description}</div>
                        ))}
                        <button
                            onClick={() => dispatch({ type: 'remove_line_items', lineItemIds: ['1', '3'] })}
                            data-testid="remove-1-3-button"
                        >
                            Remove Items 1 and 3
                        </button>
                    </div>
                );
            };

            await act(async () => {
                renderWithProviders(
                    <LineItemsProvider>
                        <RemoveSpecificComponent />
                    </LineItemsProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('3');
            });

            await act(async () => {
                await userEvent.click(screen.getByTestId('remove-1-3-button'));
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('1');
                expect(screen.queryByTestId('line-item-1')).not.toBeInTheDocument();
                expect(screen.getByTestId('line-item-2')).toBeInTheDocument();
                expect(screen.queryByTestId('line-item-3')).not.toBeInTheDocument();
            });
        });

        it('populate_line_items action is handled', async () => {
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

        it('populate_line_items keeps items the user selected before the refetch', async () => {
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

            await act(async () => {
                await userEvent.click(screen.getByTestId('toggle-button'));
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - selected');
            });

            // A background refresh (e.g. after creating a Splitwise expense) pulls
            // in a new line item and repopulates the list.
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('api/auth/me')) {
                    return Promise.resolve({
                        data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                    });
                }
                return Promise.resolve({
                    data: {
                        data: [...mockLineItems, {
                            id: '3',
                            date: 1640995200,
                            payment_method: 'Splitwise',
                            description: 'Refreshed transaction',
                            responsible_party: 'Splitwise Friend',
                            amount: 25.00,
                        }]
                    }
                });
            });

            await act(async () => {
                await userEvent.click(screen.getByTestId('refetch-button'));
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('3');
            });
            expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - selected');
            expect(screen.getByTestId('line-item-2')).toHaveTextContent('Test transaction 2 - not selected');
            expect(screen.getByTestId('line-item-3')).toHaveTextContent('Refreshed transaction - not selected');
        });

        it('populate_line_items drops a selected line item the refetch no longer returns', async () => {
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

            await act(async () => {
                await userEvent.click(screen.getByTestId('toggle-button'));
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-item-1')).toHaveTextContent('Test transaction 1 - selected');
            });

            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('api/auth/me')) {
                    return Promise.resolve({
                        data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                    });
                }
                return Promise.resolve({ data: { data: [mockLineItems[1]] } });
            });

            await act(async () => {
                await userEvent.click(screen.getByTestId('refetch-button'));
            });

            await waitFor(() => {
                expect(screen.getByTestId('line-items-count')).toHaveTextContent('1');
            });
            expect(screen.queryByTestId('line-item-1')).not.toBeInTheDocument();
            expect(screen.getByTestId('line-item-2')).toHaveTextContent('Test transaction 2 - not selected');
        });
    });

    describe('Error Handling', () => {
        it('API error is handled gracefully', async () => {
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

        it('empty state is maintained when API fails', async () => {
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
        it('state is maintained across multiple actions', async () => {
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

        it('multiple toggle operations are handled', async () => {
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
        it('correct API endpoint is used', async () => {
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

        it('different API response structures are handled', async () => {
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

    // End-to-end cover for the bug the selection-preserving populate fixes: the
    // Splitwise refresh landing mid-edit used to blank the Create Event modal.
    describe('Refresh Started By Creating A Splitwise Expense', () => {
        const splitwiseLineItem = {
            id: '3',
            date: 1640995200,
            payment_method: 'Splitwise',
            description: 'Alex paid Test transaction 1',
            responsible_party: 'Alex',
            amount: -25.00,
        };

        let serverLineItems: LineItemInterface[];
        let finishSplitwiseRefresh: () => void;

        beforeEach(() => {
            serverLineItems = mockLineItems;
            finishSplitwiseRefresh = () => { };

            mockAxiosInstance.get.mockImplementation((url: string) => {
                switch (url) {
                    case 'api/auth/me':
                        return Promise.resolve({
                            data: { id: 'user_123', email: 'test@example.com', first_name: 'Test', last_name: 'User' }
                        });
                    case 'api/line_items':
                        return Promise.resolve({ data: { data: serverLineItems } });
                    case 'api/categories':
                        return Promise.resolve({ data: { data: [{ id: 'cat_dining', name: 'Dining' }] } });
                    case 'api/tags':
                        return Promise.resolve({ data: { data: [] } });
                    case 'api/splitwise/friends':
                        return Promise.resolve({ data: { data: [{ id: 7, name: 'Alex' }] } });
                    case 'api/splitwise/current-user':
                        return Promise.resolve({ data: { data: { id: 1, name: 'Me' } } });
                    default:
                        return Promise.reject(new Error(`Unexpected GET ${url}`));
                }
            });

            mockAxiosInstance.post.mockImplementation((url: string) => {
                switch (url) {
                    case 'api/event-hints/evaluate':
                        return Promise.resolve({ data: { data: { suggestion: null } } });
                    case 'api/splitwise/expenses':
                        return Promise.resolve({ data: { id: 'splitwise_expense_1' } });
                    case 'api/refresh/account':
                        // The refresh runs in the background and finishes whenever
                        // the test decides to resolve it.
                        return new Promise((resolve) => {
                            finishSplitwiseRefresh = () => resolve({ data: { message: 'success' } });
                        });
                    default:
                        return Promise.reject(new Error(`Unexpected POST ${url}`));
                }
            });
        });

        const renderReviewPage = () => renderWithProviders(
            <LineItemsProvider>
                <LineItemsToReviewPage />
            </LineItemsProvider>
        );

        const selectFirstLineItem = async (user: ReturnType<typeof userEvent.setup>) => {
            const table = await screen.findByRole('table');
            await waitFor(() => expect(within(table).getAllByRole('checkbox')).toHaveLength(2));
            await user.click(within(table).getAllByRole('checkbox')[0]);
        };

        const createSplitwiseExpense = async (user: ReturnType<typeof userEvent.setup>) => {
            await user.click(screen.getByRole('button', { name: 'Create Splitwise Expense' }));
            const splitwiseDialog = await screen.findByRole('dialog');
            await within(splitwiseDialog).findByText('Alex');
            await user.click(within(splitwiseDialog).getAllByRole('checkbox')[0]);
            await user.click(within(splitwiseDialog).getByRole('button', { name: 'Create Expense' }));
            await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
        };

        const completeSplitwiseRefresh = async () => {
            serverLineItems = [...mockLineItems, splitwiseLineItem];
            await act(async () => {
                finishSplitwiseRefresh();
            });
            await screen.findAllByText('Alex paid Test transaction 1');
        };

        it('the refresh finishing does not reset the open Create Event modal', async () => {
            const user = userEvent.setup();
            renderReviewPage();

            await selectFirstLineItem(user);
            await createSplitwiseExpense(user);

            await user.click(screen.getByRole('button', { name: /Create Event/ }));
            const eventDialog = await screen.findByRole('dialog');
            await user.clear(within(eventDialog).getByLabelText('Event Name'));
            await user.type(within(eventDialog).getByLabelText('Event Name'), 'Dinner with Alex');
            await user.click(within(eventDialog).getByRole('combobox', { name: /category/i }));
            await user.click(await screen.findByRole('option', { name: 'Dining' }));

            await completeSplitwiseRefresh();

            // Re-query: a form reset remounts the fields, so the original nodes
            // would keep their values even after being detached from the document.
            const dialogAfterRefresh = screen.getByRole('dialog');
            expect(within(dialogAfterRefresh).getByLabelText('Event Name')).toHaveValue('Dinner with Alex');
            expect(within(dialogAfterRefresh).getByRole('combobox', { name: /category/i })).toHaveTextContent('Dining');
            expect(within(dialogAfterRefresh).getByText('$50.00')).toBeInTheDocument();
            expect(within(dialogAfterRefresh).getByRole('button', { name: 'Create Event' })).toBeEnabled();
        });

        it('the refresh finishing keeps the line item selection', async () => {
            const user = userEvent.setup();
            renderReviewPage();

            await selectFirstLineItem(user);
            await createSplitwiseExpense(user);
            await completeSplitwiseRefresh();

            const checkboxes = within(screen.getByRole('table')).getAllByRole('checkbox');
            expect(checkboxes[0]).toBeChecked();
            expect(checkboxes[1]).not.toBeChecked();
            expect(checkboxes[2]).not.toBeChecked();
        });
    });
});
