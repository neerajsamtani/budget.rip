import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import CreateManualTransactionModal from '../CreateManualTransactionModal';

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

// Mock payment methods data
const mockPaymentMethods = [
    { id: 'pm_cash', name: 'Cash', type: 'cash', is_active: true },
    { id: 'pm_venmo', name: 'Venmo', type: 'venmo', is_active: true },
    { id: 'pm_credit', name: 'Credit Card', type: 'credit', is_active: true },
];

// Mock the usePaymentMethods and useCreateManualTransaction hooks
const mockMutate = jest.fn();
const mockUsePaymentMethods = jest.fn(() => ({
    data: mockPaymentMethods,
    isLoading: false,
    isError: false,
}));
const mockUseCreateManualTransaction = jest.fn(() => ({
    mutate: mockMutate,
    isPending: false,
}));

jest.mock('../../hooks/useApi', () => ({
    ...jest.requireActual('../../hooks/useApi'),
    usePaymentMethods: () => mockUsePaymentMethods(),
    useCreateManualTransaction: () => mockUseCreateManualTransaction(),
}));

describe('CreateManualTransactionModal', () => {
    const mockOnHide = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
        // Reset mock implementations
        mockUsePaymentMethods.mockReturnValue({
            data: mockPaymentMethods,
            isLoading: false,
            isError: false,
        });
        mockUseCreateManualTransaction.mockReturnValue({
            mutate: mockMutate,
            isPending: false,
        });
    });

    describe('Rendering', () => {
        it('modal is rendered when show is true', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText('New Manual Transaction')).toBeInTheDocument();
        });

        it('modal is not rendered when show is false', () => {
            render(<CreateManualTransactionModal show={false} onHide={mockOnHide} />);

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        it('all form fields are rendered', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Person')).toBeInTheDocument();
            expect(screen.getByText('Description')).toBeInTheDocument();
            expect(screen.getByText('Amount')).toBeInTheDocument();
        });

        it('action buttons are rendered', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create transaction/i })).toBeInTheDocument();
        });

        it('description text is displayed', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Record a new transaction manually against any payment method')).toBeInTheDocument();
        });
    });

    describe('Payment Method Selection', () => {
        it('payment methods are loaded and displayed', async () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const paymentSelect = screen.getByRole('combobox');
            await userEvent.click(paymentSelect);

            await waitFor(() => {
                expect(screen.getByRole('option', { name: 'Cash' })).toBeInTheDocument();
                expect(screen.getByRole('option', { name: 'Venmo' })).toBeInTheDocument();
                expect(screen.getByRole('option', { name: 'Credit Card' })).toBeInTheDocument();
            });
        });

        it('selecting a payment method updates the form', async () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const paymentSelect = screen.getByRole('combobox');
            await userEvent.click(paymentSelect);
            await userEvent.click(screen.getByRole('option', { name: 'Venmo' }));

            expect(paymentSelect).toHaveTextContent('Venmo');
        });

        it('shows loading placeholder while payment methods load', () => {
            mockUsePaymentMethods.mockReturnValue({
                data: [],
                isLoading: true,
                isError: false,
            });

            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Loading...')).toBeInTheDocument();
        });

        it('payment method is reset when modal reopens', async () => {
            const { rerender } = render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            // Select a payment method
            const paymentSelect = screen.getByRole('combobox');
            await userEvent.click(paymentSelect);
            await userEvent.click(screen.getByRole('option', { name: 'Venmo' }));

            expect(paymentSelect).toHaveTextContent('Venmo');

            // Close and reopen modal
            rerender(<CreateManualTransactionModal show={false} onHide={mockOnHide} />);
            rerender(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            // Payment method should be reset
            const freshSelect = screen.getByRole('combobox');
            expect(freshSelect).toHaveTextContent('Select payment method');
        });
    });

    describe('Form Interactions', () => {
        it('typing in date field is allowed', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const dateInput = screen.getByLabelText('Date');
            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });

            expect(dateInput).toHaveValue('2024-01-15');
        });

        it('typing in person field is allowed', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const personInput = screen.getByLabelText('Person');
            fireEvent.change(personInput, { target: { value: 'John Doe' } });

            expect(personInput).toHaveValue('John Doe');
        });

        it('typing in description field is allowed', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const descInput = screen.getByLabelText('Description');
            fireEvent.change(descInput, { target: { value: 'Test purchase' } });

            expect(descInput).toHaveValue('Test purchase');
        });

        it('typing in amount field is allowed', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const amountInput = screen.getByLabelText('Amount');
            fireEvent.change(amountInput, { target: { value: '50.00' } });

            expect(amountInput).toHaveValue(50);
        });
    });

    describe('Form Validation', () => {
        it('shows error when submitting without payment method', async () => {
            const { toast } = require('sonner');
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const submitButton = screen.getByRole('button', { name: /create transaction/i });
            await userEvent.click(submitButton);

            expect(toast.error).toHaveBeenCalledWith('Error', {
                description: 'Please select a payment method',
                duration: 3500,
            });
            expect(mockMutate).not.toHaveBeenCalled();
        });
    });

    describe('Transaction Creation', () => {
        it('submit button shows loading state during submission', async () => {
            mockUseCreateManualTransaction.mockReturnValue({
                mutate: mockMutate,
                isPending: true,
            });

            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('button', { name: /creating/i })).toBeInTheDocument();
        });

        it('submit button is disabled during submission', async () => {
            mockUseCreateManualTransaction.mockReturnValue({
                mutate: mockMutate,
                isPending: true,
            });

            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const loadingButton = screen.getByRole('button', { name: /creating/i });
            expect(loadingButton).toBeDisabled();
        });
    });

    describe('Modal Closing', () => {
        it('onHide is called when cancel button is clicked', async () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await userEvent.click(cancelButton);

            expect(mockOnHide).toHaveBeenCalled();
        });
    });

    describe('Accessibility', () => {
        it('proper modal structure is present', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText('New Manual Transaction')).toBeInTheDocument();
        });

        it('proper form labels are present', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Person')).toBeInTheDocument();
            expect(screen.getByText('Description')).toBeInTheDocument();
            expect(screen.getByText('Amount')).toBeInTheDocument();
        });

        it('proper button labels are present', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create transaction/i })).toBeInTheDocument();
        });

        it('amount field has placeholder', () => {
            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const amountInput = screen.getByLabelText('Amount');
            expect(amountInput).toHaveAttribute('placeholder', '0.00');
        });
    });

    describe('Edge Cases', () => {
        it('handles empty payment methods gracefully', async () => {
            mockUsePaymentMethods.mockReturnValue({
                data: [],
                isLoading: false,
                isError: false,
            });

            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const paymentSelect = screen.getByRole('combobox');

            // Should not crash, just show empty select
            expect(paymentSelect).toBeInTheDocument();
        });

        it('handles undefined payment methods gracefully', async () => {
            mockUsePaymentMethods.mockReturnValue({
                data: undefined,
                isLoading: false,
                isError: false,
            });

            render(<CreateManualTransactionModal show={true} onHide={mockOnHide} />);

            const paymentSelect = screen.getByRole('combobox');

            // Should not crash
            expect(paymentSelect).toBeInTheDocument();
        });
    });
});
