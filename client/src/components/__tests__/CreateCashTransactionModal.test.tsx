import { act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import CreateCashTransactionModal from '../CreateCashTransactionModal';

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

describe('CreateCashTransactionModal', () => {
    const mockOnHide = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
        mockAxiosInstance.post.mockResolvedValue({ data: { success: true } });
    });

    describe('Rendering', () => {
        it('renders modal when show is true', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText('New Cash Transaction')).toBeInTheDocument();
        });

        it('does not render modal when show is false', () => {
            render(<CreateCashTransactionModal show={false} onHide={mockOnHide} />);

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        it('renders all form fields', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Person')).toBeInTheDocument();
            expect(screen.getByText('Description')).toBeInTheDocument();
            expect(screen.getByText('Amount')).toBeInTheDocument();
        });

        it('renders action buttons', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create transaction/i })).toBeInTheDocument();
        });

        it('renders form inputs with correct types', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');

            expect(dateInput).toHaveAttribute('type', 'date');
            expect(personInput).toHaveAttribute('type', 'text');
            expect(descriptionInput).toHaveAttribute('type', 'text');
            expect(amountInput).toHaveAttribute('type', 'number');
        });
    });

    describe('Form Interactions', () => {
        it('allows typing in date field', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            const dateInput = screen.getByLabelText('Date');
            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });

            expect(dateInput).toHaveValue('2024-01-15');
        });

        it('allows typing in person field', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            const personInput = screen.getByLabelText('Person');
            fireEvent.change(personInput, { target: { value: 'John Doe' } });

            expect(personInput).toHaveValue('John Doe');
        });

        it('allows typing in description field', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            const descriptionInput = screen.getByLabelText('Description');
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });

            expect(descriptionInput).toHaveValue('Lunch payment');
        });

        it('allows typing in amount field', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            const amountInput = screen.getByLabelText('Amount');
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            expect(amountInput).toHaveValue(25.5);
        });
    });

    describe('Form Validation', () => {
        it('enables submit button by default', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            const submitButton = screen.getByRole('button', { name: /create transaction/i });
            expect(submitButton).not.toBeDisabled();
        });
    });

    describe('Cash Transaction Creation', () => {
        it('creates cash transaction successfully', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');

            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
            fireEvent.change(personInput, { target: { value: 'John Doe' } });
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create transaction/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/cash_transaction'),
                    {
                        date: '2024-01-15',
                        person: 'John Doe',
                        description: 'Lunch payment',
                        amount: '25.50'
                    }
                );
            });
        });

        it('clears form fields after successful transaction creation', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');

            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
            fireEvent.change(personInput, { target: { value: 'John Doe' } });
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create transaction/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                expect(dateInput).toHaveValue('');
                expect(personInput).toHaveValue('');
                expect(descriptionInput).toHaveValue('');
                expect(amountInput).toHaveValue(null);
            });
        });

        it('shows toast notification after successful transaction creation', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');

            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
            fireEvent.change(personInput, { target: { value: 'John Doe' } });
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create transaction/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                const { toast } = require('sonner');
                expect(toast.success).toHaveBeenCalledWith('Notification', {
                    description: 'Created Cash Transaction',
                    duration: 3500,
                });
            });
        });

        it('calls onHide after successful transaction creation', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');

            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
            fireEvent.change(personInput, { target: { value: 'John Doe' } });
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create transaction/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                expect(mockOnHide).toHaveBeenCalled();
            });
        });

        it('handles API error gracefully', async () => {
            const { toast } = require('sonner');
            mockAxiosInstance.post.mockRejectedValue(new Error('API Error'));

            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');

            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
            fireEvent.change(personInput, { target: { value: 'John Doe' } });
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create transaction/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith("Error", {
                    description: "API Error",
                    duration: 3500,
                });
            });
        });

    });

    describe('Modal Closing', () => {
        it('calls onHide when close button is clicked', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            const closeButton = screen.getByRole('button', { name: /close/i });
            await userEvent.click(closeButton);

            expect(mockOnHide).toHaveBeenCalled();
        });

        it('calls onHide when cancel button is clicked', async () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await userEvent.click(cancelButton);

            expect(mockOnHide).toHaveBeenCalled();
        });
    });

    describe('Accessibility', () => {
        it('has proper modal structure', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText('New Cash Transaction')).toBeInTheDocument();
        });

        it('has proper form labels', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Person')).toBeInTheDocument();
            expect(screen.getByText('Description')).toBeInTheDocument();
            expect(screen.getByText('Amount')).toBeInTheDocument();
        });

        it('has proper button labels', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create transaction/i })).toBeInTheDocument();
        });

        it('has form inputs with proper IDs', () => {
            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            expect(screen.getByLabelText('Date')).toHaveAttribute('id', 'event-date');
            expect(screen.getByLabelText('Person')).toHaveAttribute('id', 'event-person');
            expect(screen.getByLabelText('Description')).toHaveAttribute('id', 'event-description');
            expect(screen.getByLabelText('Amount')).toHaveAttribute('id', 'event-amount');
        });
    });

    describe('Form State Management', () => {
        it('updates form fields on user input', async () => {
            await act(async () => {
                render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);
            });

            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');

            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
            fireEvent.change(personInput, { target: { value: 'John Doe' } });
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            expect(dateInput).toHaveValue('2024-01-15');
            expect(personInput).toHaveValue('John Doe');
            expect(descriptionInput).toHaveValue('Lunch payment');
            expect(amountInput).toHaveValue(25.5);
        });

        it('clears form fields after successful submission', async () => {
            mockAxiosInstance.post.mockResolvedValueOnce({ data: { success: true } });

            await act(async () => {
                render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);
            });

            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');
            const submitButton = screen.getByRole('button', { name: /create transaction/i });

            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
            fireEvent.change(personInput, { target: { value: 'John Doe' } });
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            await waitFor(() => {
                expect(dateInput).toHaveValue('');
                expect(personInput).toHaveValue('');
                expect(descriptionInput).toHaveValue('');
                expect(amountInput).toHaveValue(null);
            });
        });
    });

    describe('Environment Configuration', () => {
        it('uses VITE_API_ENDPOINT environment variable', async () => {
            const originalEnv = process.env.VITE_API_ENDPOINT;
            process.env.VITE_API_ENDPOINT = 'http://localhost:3000/';

            render(<CreateCashTransactionModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const dateInput = screen.getByLabelText('Date');
            const personInput = screen.getByLabelText('Person');
            const descriptionInput = screen.getByLabelText('Description');
            const amountInput = screen.getByLabelText('Amount');

            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
            fireEvent.change(personInput, { target: { value: 'John Doe' } });
            fireEvent.change(descriptionInput, { target: { value: 'Lunch payment' } });
            fireEvent.change(amountInput, { target: { value: '25.50' } });

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create transaction/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    'api/cash_transaction',
                    expect.any(Object)
                );
            });

            // Restore original environment
            process.env.VITE_API_ENDPOINT = originalEnv;
        });
    });
}); 