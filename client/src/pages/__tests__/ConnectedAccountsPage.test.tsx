import React from 'react';
import { fireEvent, mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import ConnectedAccountsPage from '../ConnectedAccountsPage';

// Mock Notification and FinancialConnectionsForm
jest.mock('../../components/Notification', () => ({ notification, setNotification }: any) => (
    notification.showNotification ? <div data-testid="notification">{notification.message}</div> : null
));
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
                expect(screen.getByText('Net Worth: $1,000.00')).toBeInTheDocument();
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
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.get.mockRejectedValueOnce(new Error('API Error'));
            render(<ConnectedAccountsPage stripePromise={mockStripePromise} />);
            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });
            consoleSpy.mockRestore();
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
                expect(screen.getByText('$1,000.00')).toBeInTheDocument();
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
}); 