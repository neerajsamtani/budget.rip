import { FinancialConnectionsSession } from '@stripe/stripe-js/types/api';
import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import FinancialConnectionsForm from '../FinancialConnectionsForm';

// Mock the Notification component before imports
jest.mock('../Notification', () => {
    return function MockNotification({ notification, setNotification }: any) {
        return notification.showNotification ? (
            <div data-testid="notification">
                {notification.heading}: {notification.message}
            </div>
        ) : null;
    };
});

// Mock Stripe
const mockCollectFinancialConnectionsAccounts = jest.fn();
const mockStripe = {
    collectFinancialConnectionsAccounts: mockCollectFinancialConnectionsAccounts,
};

jest.mock('@stripe/react-stripe-js', () => ({
    useStripe: jest.fn(() => mockStripe),
}));

describe('FinancialConnectionsForm', () => {
    const mockSetStripeAccounts = jest.fn();
    const mockFcsessSecret = 'fcsess_test_secret_123';

    const mockAccounts: FinancialConnectionsSession.Account[] = [
        {
            id: 'acc_123',
            livemode: false,
            object: 'financial_connections.account',
            display_name: 'Test Bank Account',
            institution_name: 'Test Bank',
            last4: '1234',
            status: 'active',
            supported_payment_method_types: ['us_bank_account'],
            created: 1640995200,
            balance: null,
            balance_refresh: null,
            category: 'cash',
            ownership: 'owner',
            ownership_refresh: null,
            permissions: ['payment_method', 'balances'],
            subcategory: 'checking'
        },
        {
            id: 'acc_456',
            livemode: false,
            object: 'financial_connections.account',
            display_name: 'Test Credit Card',
            institution_name: 'Test Credit Union',
            last4: '5678',
            status: 'active',
            supported_payment_method_types: ['us_bank_account'],
            created: 1640995200,
            balance: null,
            balance_refresh: null,
            category: 'credit',
            ownership: 'owner',
            ownership_refresh: null,
            permissions: ['payment_method', 'balances'],
            subcategory: 'credit_card'
        }
    ];

    beforeEach(() => {
        jest.clearAllMocks();
        mockAxiosInstance.post.mockResolvedValue({ data: { success: true } });
        mockCollectFinancialConnectionsAccounts.mockResolvedValue({
            financialConnectionsSession: {
                accounts: mockAccounts
            }
        });

        // Reset useStripe mock to return the default mockStripe
        const { useStripe } = require('@stripe/react-stripe-js');
        useStripe.mockReturnValue(mockStripe);
    });

    describe('Rendering', () => {
        it('renders connect bank button', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.getByRole('button', { name: /connect your bank/i })).toBeInTheDocument();
        });

        it('renders button with correct id', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            expect(button).toHaveAttribute('id', 'submit');
        });

        it('does not show notification initially', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.queryByTestId('notification')).not.toBeInTheDocument();
        });

        it('does not show spinner initially', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.queryByTestId('spinner')).not.toBeInTheDocument();
        });
    });

    describe('Button State Management', () => {
        it('enables button when stripe is available', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            expect(button).not.toBeDisabled();
        });

        it('disables button when stripe is not available', () => {
            // Mock stripe as null
            const { useStripe } = require('@stripe/react-stripe-js');
            useStripe.mockReturnValue(null);

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            expect(button).toBeDisabled();
        });

        it('disables button during loading', async () => {
            // Mock a slow response
            mockCollectFinancialConnectionsAccounts.mockImplementation(
                () => new Promise(resolve => setTimeout(() => resolve({
                    financialConnectionsSession: { accounts: mockAccounts }
                }), 100))
            );

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            expect(button).toBeDisabled();
        });
    });

    describe('Loading State', () => {
        it('shows spinner when loading', async () => {
            // Mock a slow response
            mockCollectFinancialConnectionsAccounts.mockImplementation(
                () => new Promise(resolve => setTimeout(() => resolve({
                    financialConnectionsSession: { accounts: mockAccounts }
                }), 100))
            );

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            expect(screen.getByTestId('spinner')).toBeInTheDocument();
        });

        it('hides spinner after loading completes', async () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            await waitFor(() => {
                expect(screen.queryByTestId('spinner')).not.toBeInTheDocument();
            });
        });
    });

    describe('Successful Account Connection', () => {
        it('calls stripe.collectFinancialConnectionsAccounts with correct secret', async () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            expect(mockCollectFinancialConnectionsAccounts).toHaveBeenCalledWith({
                clientSecret: mockFcsessSecret
            });
        });

        it('calls setStripeAccounts with returned accounts', async () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            await waitFor(() => {
                expect(mockSetStripeAccounts).toHaveBeenCalledWith(mockAccounts);
            });
        });

        it('stores accounts via API call', async () => {
            const originalEnv = process.env.REACT_APP_API_ENDPOINT;
            process.env.REACT_APP_API_ENDPOINT = 'http://localhost:3000/';

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    'http://localhost:3000/api/create_accounts',
                    mockAccounts
                );
            });

            process.env.REACT_APP_API_ENDPOINT = originalEnv;
        });

        it('logs API response data', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            const mockResponse = { data: { success: true, message: 'Accounts created' } };
            mockAxiosInstance.post.mockResolvedValue(mockResponse);

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(mockResponse.data);
            });

            consoleSpy.mockRestore();
        });
    });

    describe('Error Handling', () => {
        it('shows error notification when stripe returns error', async () => {
            const mockError = {
                error: {
                    message: 'Connection failed'
                }
            };
            mockCollectFinancialConnectionsAccounts.mockResolvedValue(mockError);

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            await waitFor(() => {
                expect(screen.getByTestId('notification')).toBeInTheDocument();
                expect(screen.getByText('Error: Connection failed Please refresh the page and try again.')).toBeInTheDocument();
            });
        });

        it('shows notification when no accounts are linked', async () => {
            mockCollectFinancialConnectionsAccounts.mockResolvedValue({
                financialConnectionsSession: {
                    accounts: []
                }
            });

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            await waitFor(() => {
                expect(screen.getByTestId('notification')).toBeInTheDocument();
                expect(screen.getByText('Error: No new accounts were linked')).toBeInTheDocument();
            });
        });

        it('handles API error gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.post.mockRejectedValue(new Error('API Error'));

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });

            consoleSpy.mockRestore();
        });

        it('does not call setStripeAccounts when there is an error', async () => {
            const mockError = {
                error: {
                    message: 'Connection failed'
                }
            };
            mockCollectFinancialConnectionsAccounts.mockResolvedValue(mockError);

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            // Wait a bit to ensure the promise resolution is handled
            await new Promise(resolve => setTimeout(resolve, 100));

            expect(mockSetStripeAccounts).not.toHaveBeenCalled();
        });

        it('returns early when stripe is not available', async () => {
            // Mock stripe as null
            const { useStripe } = require('@stripe/react-stripe-js');
            useStripe.mockReturnValue(null);

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            // Should not call any Stripe methods
            expect(mockCollectFinancialConnectionsAccounts).not.toHaveBeenCalled();
            expect(mockSetStripeAccounts).not.toHaveBeenCalled();
        });
    });

    describe('User Interactions', () => {
        it('prevents default form submission', async () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });

            // Simulate the click event
            fireEvent.click(button);

            await waitFor(() => {
                expect(mockCollectFinancialConnectionsAccounts).toHaveBeenCalled();
            });
        });
    });

    describe('Accessibility', () => {
        it('has proper button structure', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            expect(button).toBeInTheDocument();
        });

        it('has proper spinner accessibility attributes', async () => {
            // Mock a slow response
            mockCollectFinancialConnectionsAccounts.mockImplementation(
                () => new Promise(resolve => setTimeout(() => resolve({
                    financialConnectionsSession: { accounts: mockAccounts }
                }), 100))
            );

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            const spinner = screen.getByTestId('spinner');
            expect(spinner).toHaveAttribute('aria-hidden', 'true');
        });
    });

    describe('State Management', () => {
        it('initializes notification state correctly', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.queryByTestId('notification')).not.toBeInTheDocument();
        });

        it('initializes loading state correctly', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.queryByTestId('spinner')).not.toBeInTheDocument();
        });

        it('updates loading state during API call', async () => {
            // Mock a slow response
            mockCollectFinancialConnectionsAccounts.mockImplementation(
                () => new Promise(resolve => setTimeout(() => resolve({
                    financialConnectionsSession: { accounts: mockAccounts }
                }), 100))
            );

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            // Should show spinner during loading
            expect(screen.getByTestId('spinner')).toBeInTheDocument();

            // Wait for loading to complete
            await waitFor(() => {
                expect(screen.queryByTestId('spinner')).not.toBeInTheDocument();
            });
        });
    });

    describe('Environment Configuration', () => {
        it('uses REACT_APP_API_ENDPOINT environment variable', async () => {
            const originalEnv = process.env.REACT_APP_API_ENDPOINT;
            process.env.REACT_APP_API_ENDPOINT = 'https://api.example.com/';

            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            await userEvent.click(button);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    'https://api.example.com/api/create_accounts',
                    mockAccounts
                );
            });

            // Restore original environment
            process.env.REACT_APP_API_ENDPOINT = originalEnv;
        });
    });
}); 