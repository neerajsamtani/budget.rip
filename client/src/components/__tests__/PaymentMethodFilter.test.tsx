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

    // Payment method names for assertions
    const mockPaymentMethodNames = [
        'Bank of America Credit Card',
        'Chase Credit Card',
        'cash',
        'venmo',
        'splitwise'
    ];

    // Full payment method objects as returned by the API
    const mockPaymentMethodObjects = mockPaymentMethodNames.map((name, i) => ({
        id: `pm_${i}`,
        name,
        type: 'credit',
        is_active: true
    }));

    beforeEach(() => {
        jest.clearAllMocks();
        // API now returns { data: [...PaymentMethod objects...] }
        mockAxiosInstance.get.mockResolvedValue({ data: { data: mockPaymentMethodObjects } });
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
            render(<PaymentMethodFilter paymentMethod="Bank of America Credit Card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('Bank of America Credit Card');
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
                mockPaymentMethodNames.forEach(method => {
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
            rerender(<PaymentMethodFilter paymentMethod="Bank of America Credit Card" setPaymentMethod={mockSetPaymentMethod} />);

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
                expect(screen.getByRole('option', { name: 'Bank of America Credit Card' })).toBeInTheDocument();
            });

            await userEvent.click(screen.getByRole('option', { name: 'Bank of America Credit Card' }));

            expect(mockSetPaymentMethod).toHaveBeenCalledWith('Bank of America Credit Card');
        });

        it('selection of "All" option is handled correctly', async () => {
            render(<PaymentMethodFilter paymentMethod="Bank of America Credit Card" setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);
            await userEvent.click(screen.getByRole('option', { name: 'All' }));

            expect(mockSetPaymentMethod).toHaveBeenCalledWith('All');
        });

        it('display value is updated when payment method prop changes', async () => {
            const { rerender } = render(<PaymentMethodFilter paymentMethod="All" setPaymentMethod={mockSetPaymentMethod} />);

            let trigger = screen.getByRole('combobox');
            expect(trigger).toHaveTextContent('All');

            rerender(<PaymentMethodFilter paymentMethod="Chase Credit Card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('Chase Credit Card');
            });
        });

        it('rapid selection changes are handled correctly', async () => {
            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'Bank of America Credit Card' })).toBeInTheDocument();
            });
            await userEvent.click(screen.getByRole('option', { name: 'Bank of America Credit Card' }));

            await userEvent.click(trigger);
            await userEvent.click(screen.getByRole('option', { name: 'Chase Credit Card' }));

            await userEvent.click(trigger);
            await userEvent.click(screen.getByRole('option', { name: 'cash' }));

            expect(mockSetPaymentMethod).toHaveBeenCalledTimes(3);
            expect(mockSetPaymentMethod).toHaveBeenNthCalledWith(1, 'Bank of America Credit Card');
            expect(mockSetPaymentMethod).toHaveBeenNthCalledWith(2, 'Chase Credit Card');
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
                expect(screen.getByRole('option', { name: 'Bank of America Credit Card' })).toBeInTheDocument();
            });

            await userEvent.click(screen.getByRole('option', { name: 'Bank of America Credit Card' }));

            expect(customSetPaymentMethod).toHaveBeenCalledWith('Bank of America Credit Card');
        });

        it('empty payment methods array is handled correctly', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: { data: [] } });

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
                mockPaymentMethodNames.forEach(method => {
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
            mockAxiosInstance.get.mockResolvedValue({ data: { data: null } });

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
            mockAxiosInstance.get.mockResolvedValue({ data: { data: undefined } });

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
            const specialPaymentMethodNames = ['credit-card', 'debit_card', 'cash_money', 'pay-pal'];
            const specialPaymentMethodObjects = specialPaymentMethodNames.map((name, i) => ({
                id: `pm_special_${i}`,
                name,
                type: 'credit',
                is_active: true
            }));
            mockAxiosInstance.get.mockResolvedValue({ data: { data: specialPaymentMethodObjects } });

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                specialPaymentMethodNames.forEach(method => {
                    expect(screen.getByRole('option', { name: method })).toBeInTheDocument();
                });
            });
        });

        it('very long payment method names are handled correctly', async () => {
            const longPaymentMethodNames = ['very_long_payment_method_name_that_might_wrap'];
            const longPaymentMethodObjects = longPaymentMethodNames.map((name, i) => ({
                id: `pm_long_${i}`,
                name,
                type: 'credit',
                is_active: true
            }));
            mockAxiosInstance.get.mockResolvedValue({ data: { data: longPaymentMethodObjects } });

            render(<PaymentMethodFilter paymentMethod={mockPaymentMethod} setPaymentMethod={mockSetPaymentMethod} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                expect(screen.getByRole('option', { name: longPaymentMethodNames[0] })).toBeInTheDocument();
            });
        });

        it('state is maintained after prop updates', async () => {
            const { rerender } = render(<PaymentMethodFilter paymentMethod="All" setPaymentMethod={mockSetPaymentMethod} />);

            let trigger = screen.getByRole('combobox');
            expect(trigger).toHaveTextContent('All');

            rerender(<PaymentMethodFilter paymentMethod="Bank of America Credit Card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('Bank of America Credit Card');
            });

            // Payment methods should still be loaded
            await userEvent.click(trigger);
            await waitFor(() => {
                mockPaymentMethodNames.forEach(method => {
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
                mockPaymentMethodNames.forEach(method => {
                    expect(screen.getByRole('option', { name: method })).toBeInTheDocument();
                });
            });

            // Should have "All" + payment methods
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(mockPaymentMethodNames.length + 1);
        });

        it('selected value is preserved during state updates', async () => {
            render(<PaymentMethodFilter paymentMethod="Bank of America Credit Card" setPaymentMethod={mockSetPaymentMethod} />);

            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('Bank of America Credit Card');
            });

            // Should still show Bank of America Credit Card as selected
            const trigger = screen.getByRole('combobox');
            expect(trigger).toHaveTextContent('Bank of America Credit Card');
        });
    });
}); 