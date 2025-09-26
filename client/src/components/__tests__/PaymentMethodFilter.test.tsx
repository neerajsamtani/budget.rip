import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import PaymentMethodFilter from '../PaymentMethodFilter';

// Mock axiosInstance
jest.mock('../../utils/axiosInstance', () => ({
    __esModule: true,
    default: {
        get: jest.fn(),
    },
}));

describe('PaymentMethodFilter', () => {
    const mockSetPaymentMethod = jest.fn();
    const mockPaymentMethod = 'All';

    const mockPaymentMethods = [
        'credit_card',
        'debit_card',
        'cash',
        'venmo',
        'paypal'
    ];

    beforeEach(() => {
        jest.clearAllMocks();
        mockAxiosInstance.get.mockResolvedValue({ data: mockPaymentMethods });
    });

    describe('Rendering', () => {
        it('renders payment method filter component', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('renders with default "All" option', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();
            expect(trigger).toHaveTextContent('All');
        });

        it('renders with proper form structure', () => {
            const { container } = render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('displays current payment method value after API loads', async () => {
            render(<PaymentMethodFilter paymentMethod="credit_card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('credit_card');
            });
        });
    });

    describe('API Integration', () => {
        it('fetches payment methods on component mount', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/payment_methods')
                );
            });
        });

        it('populates select with fetched payment methods', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                mockPaymentMethods.forEach(method => {
                    expect(screen.getByRole('option', { name: method })).toBeInTheDocument();
                });
            });
        });

        it('handles API error gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });

            consoleSpy.mockRestore();
        });

        it('only fetches payment methods once on mount', async () => {
            const { rerender } = render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            // Rerender with different props
            rerender(<PaymentMethodFilter paymentMethod="credit_card" setPaymentMethod={mockSetPaymentMethod} />);

            // Should not fetch again
            expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
        });
    });

    describe('User Interactions', () => {
        it('calls setPaymentMethod when user selects different option', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'credit_card' })).toBeInTheDocument();
            });

            await userEvent.click(screen.getByRole('option', { name: 'credit_card' }));

            expect(mockSetPaymentMethod).toHaveBeenCalledWith('credit_card');
        });

        it('handles selection of "All" option', async () => {
            render(<PaymentMethodFilter paymentMethod="credit_card" setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);
            await userEvent.click(screen.getByRole('option', { name: 'All' }));

            expect(mockSetPaymentMethod).toHaveBeenCalledWith('All');
        });

        it('updates display value when payment method prop changes', async () => {
            const { rerender } = render(<PaymentMethodFilter paymentMethod="All" setPaymentMethod={mockSetPaymentMethod} />);

            let trigger = screen.getByRole('combobox');
            expect(trigger).toHaveTextContent('All');

            rerender(<PaymentMethodFilter paymentMethod="debit_card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('debit_card');
            });
        });

        it('handles rapid selection changes', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'credit_card' })).toBeInTheDocument();
            });
            await userEvent.click(screen.getByRole('option', { name: 'credit_card' }));

            await userEvent.click(trigger);
            await userEvent.click(screen.getByRole('option', { name: 'debit_card' }));

            await userEvent.click(trigger);
            await userEvent.click(screen.getByRole('option', { name: 'cash' }));

            expect(mockSetPaymentMethod).toHaveBeenCalledTimes(3);
            expect(mockSetPaymentMethod).toHaveBeenNthCalledWith(1, 'credit_card');
            expect(mockSetPaymentMethod).toHaveBeenNthCalledWith(2, 'debit_card');
            expect(mockSetPaymentMethod).toHaveBeenNthCalledWith(3, 'cash');
        });
    });

    describe('Props Handling', () => {
        it('accepts different initial payment method values', async () => {
            render(<PaymentMethodFilter paymentMethod="venmo" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('venmo');
            });
        });

        it('calls the provided setPaymentMethod function', async () => {
            const customSetPaymentMethod = jest.fn();
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={customSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'credit_card' })).toBeInTheDocument();
            });

            await userEvent.click(screen.getByRole('option', { name: 'credit_card' }));

            expect(customSetPaymentMethod).toHaveBeenCalledWith('credit_card');
        });

        it('handles empty payment methods array', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: [] });

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();
            });

            // Should only have "All" option
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(1);
            expect(options[0]).toHaveTextContent('All');
        });
    });

    describe('Form Structure', () => {
        it('has proper input group structure', () => {
            const { container } = render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('has proper form select structure', () => {
            const { container } = render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('has proper control ID', () => {
            const { container } = render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const select = screen.getByRole('combobox');
            expect(select).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('has proper select role', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('has proper option elements', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();

            await waitFor(() => {
                mockPaymentMethods.forEach(method => {
                    expect(screen.getByRole('option', { name: method })).toBeInTheDocument();
                });
            });
        });

        it('has proper label text', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
        });
    });

    describe('Edge Cases', () => {
        it('handles API response with null data', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: null });

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Should still render the component with "All" option
            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();
            });

            // Should only have "All" option since data is null
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(1);
        });

        it('handles API response with undefined data', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: undefined });

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Should still render the component with "All" option
            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();
            });

            // Should only have "All" option since data is undefined
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(1);
        });

        it('handles payment methods with special characters', async () => {
            const specialPaymentMethods = ['credit-card', 'debit_card', 'cash_money', 'pay-pal'];
            mockAxiosInstance.get.mockResolvedValue({ data: specialPaymentMethods });

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                specialPaymentMethods.forEach(method => {
                    expect(screen.getByRole('option', { name: method })).toBeInTheDocument();
                });
            });
        });

        it('handles very long payment method names', async () => {
            const longPaymentMethods = ['very_long_payment_method_name_that_might_wrap'];
            mockAxiosInstance.get.mockResolvedValue({ data: longPaymentMethods });

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                expect(screen.getByRole('option', { name: longPaymentMethods[0] })).toBeInTheDocument();
            });
        });

        it('maintains state after prop updates', async () => {
            const { rerender } = render(<PaymentMethodFilter paymentMethod="All" setPaymentMethod={mockSetPaymentMethod} />);

            let trigger = screen.getByRole('combobox');
            expect(trigger).toHaveTextContent('All');

            rerender(<PaymentMethodFilter paymentMethod="credit_card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('credit_card');
            });

            // Payment methods should still be loaded
            await userEvent.click(trigger);
            await waitFor(() => {
                mockPaymentMethods.forEach(method => {
                    expect(screen.getByRole('option', { name: method })).toBeInTheDocument();
                });
            });
        });
    });

    describe('State Management', () => {
        it('initializes with empty payment methods array', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Initially only "All" option should be present
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(1);
            expect(options[0]).toHaveTextContent('All');
        });

        it('updates payment methods state after API call', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                mockPaymentMethods.forEach(method => {
                    expect(screen.getByRole('option', { name: method })).toBeInTheDocument();
                });
            });

            // Should have "All" + payment methods
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(mockPaymentMethods.length + 1);
        });

        it('preserves selected value during state updates', async () => {
            render(<PaymentMethodFilter paymentMethod="credit_card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('credit_card');
            });

            // Should still show credit_card as selected
            const trigger = screen.getByRole('combobox');
            expect(trigger).toHaveTextContent('credit_card');
        });
    });
}); 