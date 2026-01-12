import userEvent from '@testing-library/user-event';
import React from 'react';
import { LineItemInterface } from '../../contexts/LineItemsContext';
import { fireEvent, render, screen, waitFor } from '../../utils/test-utils';
import LineItemDetailsModal from '../LineItemDetailsModal';

// Mock Sonner toast
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

// Mock the API hooks
const mockUpdateLineItem = jest.fn();
const mockDeleteManualTransaction = jest.fn();

jest.mock('../../hooks/useApi', () => ({
    ...jest.requireActual('../../hooks/useApi'),
    useUpdateLineItem: () => ({
        mutate: mockUpdateLineItem,
        isPending: false,
    }),
    useDeleteManualTransaction: () => ({
        mutate: mockDeleteManualTransaction,
        isPending: false,
    }),
}));

// Mock the LineItemsContext
const mockDispatch = jest.fn();
jest.mock('../../contexts/LineItemsContext', () => ({
    ...jest.requireActual('../../contexts/LineItemsContext'),
    useLineItemsDispatch: () => mockDispatch,
}));

describe('LineItemDetailsModal', () => {
    const mockOnHide = jest.fn();

    const mockLineItem: LineItemInterface = {
        id: 'li_123',
        transaction_id: 'txn_456',
        date: 1640995200,
        payment_method: 'Cash',
        description: 'Test Transaction',
        responsible_party: 'John Doe',
        amount: -50.00,
        notes: 'Initial notes',
        is_manual: false,
    };

    const mockManualLineItem: LineItemInterface = {
        ...mockLineItem,
        id: 'li_manual',
        transaction_id: 'txn_manual',
        is_manual: true,
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Rendering', () => {
        it('modal displays line item details when open', () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockLineItem}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByText('Transaction Details')).toBeInTheDocument();
            expect(screen.getByText('Test Transaction')).toBeInTheDocument();
            expect(screen.getByText('Cash')).toBeInTheDocument();
            expect(screen.getByText('John Doe')).toBeInTheDocument();
            expect(screen.getByText('$50.00')).toBeInTheDocument();
        });

        it('modal displays notes when present', () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockLineItem}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByText('Initial notes')).toBeInTheDocument();
        });

        it('modal shows "Add Notes" button when no notes exist', () => {
            const lineItemWithoutNotes = { ...mockLineItem, notes: undefined };
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={lineItemWithoutNotes}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByRole('button', { name: /add notes/i })).toBeInTheDocument();
        });

        it('modal shows "Edit Notes" button when notes exist', () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockLineItem}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByRole('button', { name: /edit notes/i })).toBeInTheDocument();
        });
    });

    describe('Delete functionality', () => {
        it('delete button is shown only for manual transactions', () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockManualLineItem}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
        });

        it('delete button is hidden for non-manual transactions', () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockLineItem}
                    onHide={mockOnHide}
                />
            );

            expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
        });

        it('delete button calls mutation with transaction_id', async () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockManualLineItem}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            expect(mockDeleteManualTransaction).toHaveBeenCalledWith(
                'txn_manual',
                expect.any(Object)
            );
        });
    });

    describe('Notes editing', () => {
        it('clicking edit notes enters edit mode', async () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockLineItem}
                    onHide={mockOnHide}
                />
            );

            const editButton = screen.getByRole('button', { name: /edit notes/i });
            await userEvent.click(editButton);

            expect(screen.getByText('Edit Notes')).toBeInTheDocument();
            expect(screen.getByRole('textbox')).toBeInTheDocument();
        });

        it('save button calls update mutation with notes', async () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockLineItem}
                    onHide={mockOnHide}
                />
            );

            // Enter edit mode
            await userEvent.click(screen.getByRole('button', { name: /edit notes/i }));

            // Clear and type new notes
            const textarea = screen.getByRole('textbox');
            fireEvent.change(textarea, { target: { value: 'Updated notes' } });

            // Save
            await userEvent.click(screen.getByRole('button', { name: /save/i }));

            expect(mockUpdateLineItem).toHaveBeenCalledWith(
                { lineItemId: 'li_123', notes: 'Updated notes' },
                expect.any(Object)
            );
        });

        it('cancel returns to view mode without saving', async () => {
            render(
                <LineItemDetailsModal
                    show={true}
                    lineItem={mockLineItem}
                    onHide={mockOnHide}
                />
            );

            // Enter edit mode
            await userEvent.click(screen.getByRole('button', { name: /edit notes/i }));

            // Type something
            const textarea = screen.getByRole('textbox');
            fireEvent.change(textarea, { target: { value: 'some new text' } });

            // Cancel
            await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

            // Should be back to view mode
            expect(screen.getByText('Transaction Details')).toBeInTheDocument();
            expect(mockUpdateLineItem).not.toHaveBeenCalled();
        });
    });
});
