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
        it('payment method filter component is displayed', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('default "All" option is rendered', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();
            expect(trigger).toHaveTextContent('All');
        });

        it('proper form structure is rendered', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('current payment method value is displayed after API loads', async () => {
            render(<PaymentMethodFilter paymentMethod="credit_card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('credit_card');
            });
        });
    });

    describe('API Integration', () => {
        it('payment methods are fetched on component mount', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/payment_methods')
                );
            });
        });

        it('select is populated with fetched payment methods', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                mockPaymentMethods.forEach(method => {
                    expect(screen.getByRole('option', { name: method })).toBeInTheDocument();
                });
            });
        });

        it('API error is handled gracefully', async () => {
            const { toast } = require('sonner');
            mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith("Error", {
                    description: "API Error",
                    duration: 3500,
                });
            });
        });

        it('payment methods are fetched only once on mount', async () => {
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
        it('setPaymentMethod is called when user selects different option', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'credit_card' })).toBeInTheDocument();
            });

            await userEvent.click(screen.getByRole('option', { name: 'credit_card' }));

            expect(mockSetPaymentMethod).toHaveBeenCalledWith('credit_card');
        });

        it('selection of "All" option is handled correctly', async () => {
            render(<PaymentMethodFilter paymentMethod="credit_card" setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);
            await userEvent.click(screen.getByRole('option', { name: 'All' }));

            expect(mockSetPaymentMethod).toHaveBeenCalledWith('All');
        });

        it('display value is updated when payment method prop changes', async () => {
            const { rerender } = render(<PaymentMethodFilter paymentMethod="All" setPaymentMethod={mockSetPaymentMethod} />);

            let trigger = screen.getByRole('combobox');
            expect(trigger).toHaveTextContent('All');

            rerender(<PaymentMethodFilter paymentMethod="debit_card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('debit_card');
            });
        });

        it('rapid selection changes are handled correctly', async () => {
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
        it('different initial payment method values are accepted', async () => {
            render(<PaymentMethodFilter paymentMethod="venmo" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('venmo');
            });
        });

        it('provided setPaymentMethod function is called', async () => {
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

        it('empty payment methods array is handled correctly', async () => {
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
        it('proper input group structure is present', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('proper form select structure is present', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('proper control ID is set', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const select = screen.getByRole('combobox');
            expect(select).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('proper select role is set', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('proper option elements are present', async () => {
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

        it('proper label text is displayed', () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
        });
    });

    describe('Edge Cases', () => {
        it('API response with null data is handled correctly', async () => {
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

        it('API response with undefined data is handled correctly', async () => {
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

        it('payment methods with special characters are handled correctly', async () => {
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

        it('very long payment method names are handled correctly', async () => {
            const longPaymentMethods = ['very_long_payment_method_name_that_might_wrap'];
            mockAxiosInstance.get.mockResolvedValue({ data: longPaymentMethods });

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                expect(screen.getByRole('option', { name: longPaymentMethods[0] })).toBeInTheDocument();
            });
        });

        it('state is maintained after prop updates', async () => {
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
        it('payment methods array is initialized as empty', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Initially only "All" option should be present
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(1);
            expect(options[0]).toHaveTextContent('All');
        });

        it('payment methods state is updated after API call', async () => {
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

        it('selected value is preserved during state updates', async () => {
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