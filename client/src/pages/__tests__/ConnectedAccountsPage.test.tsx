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
    { venmo: [{ username: 'user1', last_refreshed_at: 1700000000 }] },
    { splitwise: [{ username: 'swuser1', last_refreshed_at: 1700000000 }] },
    {
        stripe: [
            {
                institution_name: 'Bank',
                display_name: 'Checking',
                last4: '1234',
                _id: 'stripe-1',
                id: 'stripe-1',
                status: 'active',
            },
            {
                institution_name: 'Bank',
                display_name: 'Savings',
                last4: '5678',
                _id: 'stripe-2',
                id: 'stripe-2',
                status: 'inactive',
            },
        ],
    },
];
const mockAccountsAndBalances = {
    'stripe-1': { balance: 1000, as_of: 1700000000, status: 'active' },
    'stripe-2': { balance: 2000, as_of: 1700000000, status: 'inactive', can_relink: true },
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
            mockAxiosInstance.get.mockRejectedValueOnce(new Error('API Error'));
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            // TanStack Query handles the error internally
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalled();
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

        it('handles missing balance and date data gracefully', async () => {
            const accountsWithMissingData = [
                {
                    stripe: [
                        {
                            institution_name: 'NewBank',
                            display_name: 'Checking',
                            last4: '9999',
                            _id: 'stripe-new',
                            id: 'stripe-new',
                            status: 'active',
                        },
                    ],
                },
            ];
            const balancesWithMissingData = {
                'stripe-new': { balance: null, as_of: null, status: 'active' },
            };

            mockAxiosInstance.get.mockImplementation((url: string) => {
                if (url.includes('connected_accounts')) return Promise.resolve({ data: accountsWithMissingData });
                if (url.includes('accounts_and_balances')) return Promise.resolve({ data: balancesWithMissingData });
                return Promise.resolve({ data: {} });
            });

            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                expect(screen.getByText(/NewBank Checking 9999/)).toBeInTheDocument();
                // Should show em dash (—) instead of $0.00 or Jan 1, 1970
                const emDashes = screen.getAllByText('—');
                expect(emDashes.length).toBeGreaterThanOrEqual(2); // One for balance, one for date
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
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('relink_account')
                );
            });
        });

        it('refreshes a stripe account when refresh button is clicked', async () => {
            const { toast } = require('sonner');
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                expect(screen.getByText(/Bank Checking 1234/)).toBeInTheDocument();
            });

            const refreshButtons = screen.getAllByRole('button');
            const stripeRefreshBtn = refreshButtons.find(btn =>
                btn.querySelector('svg') &&
                btn.closest('tr')?.textContent?.includes('Bank Checking 1234')
            );

            expect(stripeRefreshBtn).toBeDefined();
            fireEvent.click(stripeRefreshBtn!);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('refresh/account'),
                    expect.objectContaining({
                        accountId: 'stripe-1',
                        source: 'stripe'
                    })
                );
            });

            await waitFor(() => {
                expect(toast.success).toHaveBeenCalledWith(
                    'Success',
                    expect.objectContaining({
                        description: 'Account data refreshed successfully'
                    })
                );
            });
        });

        it('refreshes a venmo account when refresh button is clicked', async () => {
            const { toast } = require('sonner');
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                expect(screen.getByText(/Venmo - user1/)).toBeInTheDocument();
            });

            const refreshButtons = screen.getAllByRole('button');
            const venmoRefreshBtn = refreshButtons.find(btn =>
                btn.querySelector('svg') &&
                btn.closest('tr')?.textContent?.includes('Venmo - user1')
            );

            expect(venmoRefreshBtn).toBeDefined();
            fireEvent.click(venmoRefreshBtn!);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('refresh/account'),
                    expect.objectContaining({
                        accountId: 'venmo-user1',
                        source: 'venmo'
                    })
                );
            });
        });

        it('shows error toast when refresh fails', async () => {
            const { toast } = require('sonner');
            mockAxiosInstance.post.mockImplementation((url: string) => {
                if (url.includes('refresh/account')) {
                    return Promise.reject(new Error('Refresh failed'));
                }
                return Promise.resolve({ data: { clientSecret: 'secret' } });
            });

            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                expect(screen.getByText(/Bank Checking 1234/)).toBeInTheDocument();
            });

            const refreshButtons = screen.getAllByRole('button');
            const stripeRefreshBtn = refreshButtons.find(btn =>
                btn.querySelector('svg') &&
                btn.closest('tr')?.textContent?.includes('Bank Checking 1234')
            );

            fireEvent.click(stripeRefreshBtn!);

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith(
                    'Error',
                    expect.objectContaining({
                        description: 'Refresh failed'
                    })
                );
            });
        });

        it('disables refresh button for inactive stripe accounts', async () => {
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);

            await waitFor(() => {
                const accounts = screen.getAllByText(/Bank Savings 5678/);
                expect(accounts.length).toBeGreaterThan(0);
            });

            const refreshButtons = screen.getAllByRole('button');
            const inactiveAccountRefreshBtn = refreshButtons.find(btn =>
                btn.querySelector('svg') &&
                btn.closest('tr')?.textContent?.includes('Bank Savings 5678')
            );

            expect(inactiveAccountRefreshBtn).toBeDefined();
            expect(inactiveAccountRefreshBtn).toBeDisabled();
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
}); 