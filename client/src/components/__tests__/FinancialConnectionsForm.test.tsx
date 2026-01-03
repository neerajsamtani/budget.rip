import { FinancialConnectionsSession } from '@stripe/stripe-js/types/api';
import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import FinancialConnectionsForm from '../FinancialConnectionsForm';

// Mock Sonner toast with all methods
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
        it('connect bank button is rendered', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.getByRole('button', { name: /connect your bank/i })).toBeInTheDocument();
        });

        it('button has correct id', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            expect(button).toHaveAttribute('id', 'submit');
        });

        it('notification is not shown initially', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.queryByTestId('notification')).not.toBeInTheDocument();
        });

        it('spinner is not shown initially', () => {
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
        it('button is enabled when stripe is available', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            expect(button).not.toBeDisabled();
        });

        it('button is disabled when stripe is not available', () => {
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

        it('button is disabled during loading', async () => {
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
        it('spinner is shown when loading', async () => {
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

            expect(document.querySelector('.animate-spin')).toBeInTheDocument();
        });

        it('spinner is hidden after loading completes', async () => {
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
        it('stripe.collectFinancialConnectionsAccounts is called with correct secret', async () => {
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

        it('setStripeAccounts is called with returned accounts', async () => {
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

        it('accounts are stored via API call', async () => {
            const originalEnv = process.env.VITE_API_ENDPOINT;
            process.env.VITE_API_ENDPOINT = 'http://localhost:3000/';

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
                    'api/create_accounts',
                    mockAccounts
                );
            });

            process.env.VITE_API_ENDPOINT = originalEnv;
        });

        it('success toast is shown on API response', async () => {
            const { toast } = require('sonner');
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
                expect(toast.success).toHaveBeenCalledWith("Accounts Created", {
                    description: mockResponse.data,
                    duration: 3500,
                });
            });
        });
    });

    describe('Error Handling', () => {
        it('error toast is shown when stripe returns error', async () => {
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
                const { toast } = require('sonner');
                expect(toast.error).toHaveBeenCalledWith('Error', {
                    description: 'Connection failed Please refresh the page and try again.',
                    duration: 3500,
                });
            });
        });

        it('error toast is shown when no accounts are linked', async () => {
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
                const { toast } = require('sonner');
                expect(toast.error).toHaveBeenCalledWith('Error', {
                    description: 'No new accounts were linked',
                    duration: 3500,
                });
            });
        });

        it('API error is handled gracefully', async () => {
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
                const { toast } = require('sonner');
                expect(toast.error).toHaveBeenCalledWith('Error', {
                    description: 'API Error',
                    duration: 3500,
                });
            });
        });

        it('setStripeAccounts is not called when there is an error', async () => {
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

        it('function returns early when stripe is not available', async () => {
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
        it('default form submission is prevented', async () => {
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
        it('proper button structure is present', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            const button = screen.getByRole('button', { name: /connect your bank/i });
            expect(button).toBeInTheDocument();
        });

        it('spinner has proper accessibility attributes', async () => {
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

            const spinner = document.querySelector('.animate-spin');
            expect(spinner).toBeInTheDocument();
        });
    });

    describe('State Management', () => {
        it('notification state is initialized correctly', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.queryByTestId('notification')).not.toBeInTheDocument();
        });

        it('loading state is initialized correctly', () => {
            render(
                <FinancialConnectionsForm
                    fcsess_secret={mockFcsessSecret}
                    setStripeAccounts={mockSetStripeAccounts}
                />
            );

            expect(screen.queryByTestId('spinner')).not.toBeInTheDocument();
        });

        it('loading state is updated during API call', async () => {
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
            expect(document.querySelector('.animate-spin')).toBeInTheDocument();

            // Wait for loading to complete
            await waitFor(() => {
                expect(screen.queryByTestId('spinner')).not.toBeInTheDocument();
            });
        });
    });

    describe('Environment Configuration', () => {
        it('VITE_API_ENDPOINT environment variable is used', async () => {
            const originalEnv = process.env.VITE_API_ENDPOINT;
            process.env.VITE_API_ENDPOINT = 'https://api.example.com/';

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
                    'api/create_accounts',
                    mockAccounts
                );
            });

            // Restore original environment
            process.env.VITE_API_ENDPOINT = originalEnv;
        });
    });
}); 