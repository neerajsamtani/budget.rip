import userEvent from '@testing-library/user-event';
import React from 'react';
import { act, mockAxiosInstance, render, screen, waitFor, within } from '../../utils/test-utils';
import { LineItemsProvider } from '../../contexts/LineItemsContext';
import LineItemsToReviewPage from '../LineItemsToReviewPage';

jest.mock('../../contexts/AuthContext', () => ({
    useAuth: () => ({ isAuthenticated: true }),
}));

jest.mock('sonner', () => {
    const mockToast = jest.fn();
    return {
        toast: Object.assign(mockToast, {
            success: jest.fn(),
            error: jest.fn(),
            info: jest.fn(),
            warning: jest.fn(),
        }),
    };
});

const dinnerLineItem = {
    id: '1',
    date: 1640995200,
    payment_method: 'credit_card',
    description: 'Restaurant Dinner',
    responsible_party: 'Restaurant',
    amount: 50.0,
};

const groceriesLineItem = {
    id: '2',
    date: 1640995200,
    payment_method: 'credit_card',
    description: 'Groceries',
    responsible_party: 'Supermarket',
    amount: 20.0,
};

// The line item the Splitwise refresh pulls in after the expense is created
const splitwiseLineItem = {
    id: '3',
    date: 1640995200,
    payment_method: 'Splitwise',
    description: 'Alex paid Restaurant Dinner',
    responsible_party: 'Alex',
    amount: -25.0,
};

describe('creating a Splitwise expense while reviewing line items', () => {
    let serverLineItems: typeof dinnerLineItem[];
    let finishSplitwiseRefresh: () => void;

    beforeEach(() => {
        serverLineItems = [dinnerLineItem, groceriesLineItem];
        finishSplitwiseRefresh = () => { };

        mockAxiosInstance.get.mockImplementation((url: string) => {
            switch (url) {
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
                    // The refresh runs in the background and finishes whenever the
                    // test decides to resolve it.
                    return new Promise((resolve) => {
                        finishSplitwiseRefresh = () => resolve({ data: { message: 'success' } });
                    });
                default:
                    return Promise.reject(new Error(`Unexpected POST ${url}`));
            }
        });
    });

    const renderPage = () => render(
        <LineItemsProvider>
            <LineItemsToReviewPage />
        </LineItemsProvider>
    );

    const selectDinnerLineItem = async (user: ReturnType<typeof userEvent.setup>) => {
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

    const openCreateEventModal = async (user: ReturnType<typeof userEvent.setup>) => {
        await user.click(screen.getByRole('button', { name: /Create Event/ }));
        return screen.findByRole('dialog');
    };

    const completeSplitwiseRefresh = async () => {
        serverLineItems = [dinnerLineItem, groceriesLineItem, splitwiseLineItem];
        await act(async () => {
            finishSplitwiseRefresh();
        });
        await screen.findAllByText('Alex paid Restaurant Dinner');
    };

    it('the Splitwise refresh finishing does not reset the open Create Event modal', async () => {
        const user = userEvent.setup();
        renderPage();

        await selectDinnerLineItem(user);
        await createSplitwiseExpense(user);

        const eventDialog = await openCreateEventModal(user);
        await user.clear(within(eventDialog).getByLabelText('Event Name'));
        await user.type(within(eventDialog).getByLabelText('Event Name'), 'Dinner with Alex');
        await user.click(within(eventDialog).getByRole('combobox', { name: /category/i }));
        await user.click(await screen.findByRole('option', { name: 'Dining' }));

        await completeSplitwiseRefresh();

        // Re-query: a form reset remounts the fields, so the original nodes would
        // keep their values even after being detached from the document.
        const dialogAfterRefresh = screen.getByRole('dialog');
        expect(within(dialogAfterRefresh).getByLabelText('Event Name')).toHaveValue('Dinner with Alex');
        expect(within(dialogAfterRefresh).getByRole('combobox', { name: /category/i })).toHaveTextContent('Dining');
        expect(within(dialogAfterRefresh).getByText('$50.00')).toBeInTheDocument();
        expect(within(dialogAfterRefresh).getByRole('button', { name: 'Create Event' })).toBeEnabled();
    });

    it('the Splitwise refresh finishing keeps the line item selection', async () => {
        const user = userEvent.setup();
        renderPage();

        await selectDinnerLineItem(user);
        await createSplitwiseExpense(user);
        await completeSplitwiseRefresh();

        const table = screen.getByRole('table');
        const checkboxes = within(table).getAllByRole('checkbox');
        expect(checkboxes[0]).toBeChecked();
        expect(checkboxes[1]).not.toBeChecked();
        expect(checkboxes[2]).not.toBeChecked();
    });
});
