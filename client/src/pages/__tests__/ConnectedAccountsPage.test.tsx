import React from 'react';
import { fireEvent, mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import ConnectedAccountsPage from '../ConnectedAccountsPage';

// Mock Notification and FinancialConnectionsForm
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

jest.mock('../../components/FinancialConnectionsForm', () => ({ fcsess_secret, setStripeAccounts }: any) => (
    <div data-testid="fc-form">FinancialConnectionsForm</div>
));

const mockStripePromise = Promise.resolve(null);

const mockConnectedAccounts = [
    { venmo: ['user1'] },
    { splitwise: ['swuser1'] },
    {
        stripe: [
            {
                institution_name: 'Bank',
                display_name: 'Checking',
                last4: '1234',
                _id: 'stripe-1',
                status: 'active',
            },
            {
                institution_name: 'Bank',
                display_name: 'Savings',
                last4: '5678',
                _id: 'stripe-2',
                status: 'inactive',
            },
        ],
    },
];
const mockAccountsAndBalances = {
    'stripe-1': { balance: 1000, as_of: 1700000000, status: 'active' },
    'stripe-2': { balance: 2000, as_of: 1700000000, status: 'inactive' },
};

describe('ConnectedAccountsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        process.env.VITE_API_ENDPOINT = 'http://localhost:5000/';
        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url.includes('connected_accounts')) return Promise.resolve({ data: mockConnectedAccounts });
            if (url.includes('accounts_and_balances')) return Promise.resolve({ data: mockAccountsAndBalances });
            if (url.includes('relink_account')) return Promise.resolve({ data: { clientSecret: 'secret' } });
            if (url.includes('subscribe_to_account')) return Promise.resolve({ data: { success: true } });
            return Promise.resolve({ data: {} });
        });
        mockAxiosInstance.post.mockResolvedValue({ data: { clientSecret: 'secret' } });
    });

    describe('Rendering', () => {
        it('renders page title and connect button', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Connected Accounts');
            expect(screen.getByRole('button', { name: /connect a new account/i })).toBeInTheDocument();
        });

        it('renders tables and net worth', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                expect(screen.getByText('Net Worth:')).toBeInTheDocument();
                expect(screen.getAllByText('$1,000.00').length).toBeGreaterThanOrEqual(1);
                expect(screen.getByText('Inactive Accounts')).toBeInTheDocument();
                expect(screen.getAllByRole('table').length).toBeGreaterThanOrEqual(2);
            });
        });
    });

    describe('API Integration', () => {
        it('fetches connected accounts and balances on mount', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('connected_accounts')
                );
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('accounts_and_balances')
                );
            });
        });

        it('handles API errors gracefully', async () => {
            const { toast } = require('sonner');
            mockAxiosInstance.get.mockRejectedValueOnce(new Error('API Error'));
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith("Error", {
                    description: "API Error",
                    duration: 3500,
                });
            });
        });
    });

    describe('Data Display', () => {
        it('displays venmo and splitwise accounts', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                expect(screen.getByText(/Venmo - user1/)).toBeInTheDocument();
                expect(screen.getByText(/Splitwise - swuser1/)).toBeInTheDocument();
            });
        });

        it('displays stripe accounts with status and balance', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                expect(screen.getByText(/Bank Checking 1234/)).toBeInTheDocument();
                expect(screen.getByText('Active')).toBeInTheDocument();
                // Check for balance amount within the table context
                const balanceCells = screen.getAllByText('$1,000.00');
                expect(balanceCells.length).toBeGreaterThanOrEqual(1);
            });
        });

        it('shows no connected accounts message if none', async () => {
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('connected_accounts')) return Promise.resolve({ data: [] });
                if (url.includes('accounts_and_balances')) return Promise.resolve({ data: {} });
                return Promise.resolve({ data: {} });
            });
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                expect(screen.getByText(/No connected accounts found/)).toBeInTheDocument();
            });
        });
    });

    describe('User Interactions', () => {
        it('creates a new session when connect button is clicked', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            const btn = screen.getByRole('button', { name: /connect a new account/i });
            fireEvent.click(btn);
            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('create-fc-session')
                );
            });
        });

        it('reactivates an inactive account', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                const reactivateBtn = screen.getAllByRole('button', { name: /reactivate/i })[0];
                fireEvent.click(reactivateBtn);
            });
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('relink_account')
                );
            });
        });
    });

    describe('Accessibility', () => {
        it('has proper heading and table structure', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
            await waitFor(() => {
                expect(screen.getAllByRole('table').length).toBeGreaterThanOrEqual(2);
            });
        });
    });

    describe('Refresh Single Account', () => {
        it('refreshes venmo account when refresh button is clicked', async () => {
            const mockLineItems = [{ id: 'li_1', amount: 100 }];
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('connected_accounts')) return Promise.resolve({ data: mockConnectedAccounts });
                if (url.includes('accounts_and_balances')) return Promise.resolve({ data: mockAccountsAndBalances });
                if (url.includes('account/venmo/refresh')) return Promise.resolve({ data: { data: mockLineItems } });
                return Promise.resolve({ data: {} });
            });

            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                expect(screen.getByText(/Venmo - user1/)).toBeInTheDocument();
            });

            const refreshButtons = screen.getAllByRole('button', { name: /refresh/i });
            const venmoRefreshButton = refreshButtons[0];
            fireEvent.click(venmoRefreshButton);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/account/venmo/refresh')
                );
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('accounts_and_balances')
                );
            });
        });

        it('refreshes splitwise account when refresh button is clicked', async () => {
            const mockLineItems = [{ id: 'li_1', amount: 100 }];
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('connected_accounts')) return Promise.resolve({ data: mockConnectedAccounts });
                if (url.includes('accounts_and_balances')) return Promise.resolve({ data: mockAccountsAndBalances });
                if (url.includes('account/splitwise/refresh')) return Promise.resolve({ data: { data: mockLineItems } });
                return Promise.resolve({ data: {} });
            });

            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                expect(screen.getByText(/Splitwise - swuser1/)).toBeInTheDocument();
            });

            const refreshButtons = screen.getAllByRole('button', { name: /refresh/i });
            const splitwiseRefreshButton = refreshButtons[1];
            fireEvent.click(splitwiseRefreshButton);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/account/splitwise/refresh')
                );
            });
        });

        it('refreshes stripe account when refresh button is clicked', async () => {
            const mockLineItems = [{ id: 'li_1', amount: 100 }];
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('connected_accounts')) return Promise.resolve({ data: mockConnectedAccounts });
                if (url.includes('accounts_and_balances')) return Promise.resolve({ data: mockAccountsAndBalances });
                if (url.includes('account/stripe/stripe-1/refresh')) return Promise.resolve({ data: { data: mockLineItems } });
                return Promise.resolve({ data: {} });
            });

            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                expect(screen.getByText(/Bank Checking 1234/)).toBeInTheDocument();
            });

            const refreshButtons = screen.getAllByRole('button', { name: /refresh/i });
            const stripeRefreshButton = refreshButtons[2];
            fireEvent.click(stripeRefreshButton);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/account/stripe/stripe-1/refresh')
                );
            });
        });

        it('disables refresh button while refreshing', async () => {
            const mockLineItems = [{ id: 'li_1', amount: 100 }];
            let resolveRefresh: any;
            const refreshPromise = new Promise((resolve) => {
                resolveRefresh = resolve;
            });

            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('connected_accounts')) return Promise.resolve({ data: mockConnectedAccounts });
                if (url.includes('accounts_and_balances')) return Promise.resolve({ data: mockAccountsAndBalances });
                if (url.includes('account/venmo/refresh')) return refreshPromise;
                return Promise.resolve({ data: {} });
            });

            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                expect(screen.getByText(/Venmo - user1/)).toBeInTheDocument();
            });

            const refreshButtons = screen.getAllByRole('button', { name: /refresh/i });
            const venmoRefreshButton = refreshButtons[0];
            fireEvent.click(venmoRefreshButton);

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /refreshing\.\.\./i })).toBeDisabled();
            });

            // Resolve the refresh
            resolveRefresh({ data: { data: mockLineItems } });

            await waitFor(() => {
                expect(screen.queryByRole('button', { name: /refreshing\.\.\./i })).not.toBeInTheDocument();
            });
        });

        it('handles refresh error gracefully', async () => {
            const { toast } = require('sonner');
            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('connected_accounts')) return Promise.resolve({ data: mockConnectedAccounts });
                if (url.includes('accounts_and_balances')) return Promise.resolve({ data: mockAccountsAndBalances });
                if (url.includes('account/venmo/refresh')) return Promise.reject(new Error('Refresh failed'));
                return Promise.resolve({ data: {} });
            });

            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                expect(screen.getByText(/Venmo - user1/)).toBeInTheDocument();
            });

            const refreshButtons = screen.getAllByRole('button', { name: /refresh/i });
            const venmoRefreshButton = refreshButtons[0];
            fireEvent.click(venmoRefreshButton);

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith("Error", {
                    description: "Error refreshing venmo account",
                    duration: 3500,
                });
            });
        });
    });
}); 