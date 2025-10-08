import { act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { useLineItems, useLineItemsDispatch } from '../../contexts/LineItemsContext';
import { getPrefillFromLineItems } from '../../data/EventHints';
import defaultNameCleanup from '../../utils/stringHelpers';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import CreateEventModal from '../CreateEventModal';

// Mock the string helpers first, before any other mocks or imports
jest.mock('../../utils/stringHelpers', () => ({
    __esModule: true,
    default: jest.fn((str) => str), // just return the string as-is
}));

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

// Mock the context
jest.mock('../../contexts/LineItemsContext', () => ({
    useLineItems: jest.fn(),
    useLineItemsDispatch: jest.fn(),
}));

// Mock the data utilities
jest.mock('../../data/EventHints', () => ({
    getPrefillFromLineItems: jest.fn(),
}));

const mockUseLineItems = useLineItems as jest.MockedFunction<typeof useLineItems>;
const mockUseLineItemsDispatch = useLineItemsDispatch as jest.MockedFunction<typeof useLineItemsDispatch>;

const mockGetPrefillFromLineItems = getPrefillFromLineItems as jest.MockedFunction<typeof getPrefillFromLineItems>;

const mockLineItems = [
    {
        _id: '1',
        id: '1',
        date: 1640995200,
        payment_method: 'credit_card',
        description: 'Test transaction 1',
        responsible_party: 'Test Store 1',
        amount: 50.00,
        isSelected: true,
    },
    {
        _id: '2',
        id: '2',
        date: 1640995200,
        payment_method: 'cash',
        description: 'Test transaction 2',
        responsible_party: 'Test Store 2',
        amount: 100.00,
        isSelected: true,
    },
    {
        _id: '3',
        id: '3',
        date: 1640995200,
        payment_method: 'debit_card',
        description: 'Test transaction 3',
        responsible_party: 'Test Store 3',
        amount: 25.00,
        isSelected: false,
    }
];

const mockDispatch = jest.fn();

const mockDefaultNameCleanup = defaultNameCleanup as jest.MockedFunction<typeof defaultNameCleanup>;

describe('CreateEventModal', () => {
    const mockOnHide = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
        mockUseLineItems.mockReturnValue(mockLineItems);
        mockUseLineItemsDispatch.mockReturnValue(mockDispatch);
        mockGetPrefillFromLineItems.mockReturnValue(null);
        mockDefaultNameCleanup.mockImplementation((str) => str);
        mockAxiosInstance.post.mockResolvedValue({ data: { name: 'Test Event', success: true } });
    });

    describe('Rendering', () => {
        it('renders modal when show is true', () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText('New Event Details')).toBeInTheDocument();
        });

        it('does not render modal when show is false', () => {
            render(<CreateEventModal show={false} onHide={mockOnHide} />);

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        it('renders all form fields', () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Event Name')).toBeInTheDocument();
            expect(screen.getByText('Category')).toBeInTheDocument();
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByText('Override Date (optional)')).toBeInTheDocument();
            expect(screen.getByText('Duplicate Transaction')).toBeInTheDocument();
        });

        it('renders all category options', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const options = [
                'All', 'Alcohol', 'Dining', 'Entertainment', 'Forma', 'Groceries',
                'Hobbies', 'Income', 'Investment', 'Medical', 'Rent', 'Shopping',
                'Subscription', 'Transfer', 'Transit', 'Travel'
            ];

            await waitFor(() => {
                options.forEach(option => {
                    expect(screen.getByRole('option', { name: option })).toBeInTheDocument();
                });
            });
        });

        it('renders action buttons', () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });

        it('shows total amount from selected line items', () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Total:')).toBeInTheDocument();
            expect(screen.getByText('$150.00')).toBeInTheDocument();
        });
    });

    describe('Form Interactions', () => {
        it('allows typing in name field', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event Name' } });

            expect(nameInput).toHaveValue('Test Event Name');
        });

        it('allows selecting category', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            expect(categorySelect).toHaveTextContent('Dining');
        });

        it('allows setting date', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const dateInput = screen.getByLabelText('Override Date (optional)');
            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });

            expect(dateInput).toHaveValue('2024-01-15');
        });

        it('allows toggling duplicate transaction checkbox', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);

            expect(checkbox).toBeChecked();
        });

        it('updates total when duplicate transaction is checked', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            // Initial total should be $150.00 (50 + 100)
            expect(screen.getByText('Total:')).toBeInTheDocument();
            expect(screen.getByText('$150.00')).toBeInTheDocument();

            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);

            // Total should be $75 (half of 150)
            expect(screen.getByText('Total:')).toBeInTheDocument();
            expect(screen.getByText('$75.00')).toBeInTheDocument();
        });
    });

    describe('Tag Management', () => {
        it('allows adding tags by pressing Enter', async () => {
            mockDefaultNameCleanup.mockImplementation((str) => str);
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const tagInput = screen.getByPlaceholderText('Type a tag and press Enter to add');
            fireEvent.change(tagInput, { target: { value: 'important' } });
            fireEvent.keyDown(tagInput, { key: 'Enter' });

            // Look for the tag badge specifically
            expect(screen.getByText('important')).toBeInTheDocument();
            expect(tagInput).toHaveValue('');
        });

        it('does not add empty tags', async () => {
            mockDefaultNameCleanup.mockImplementation((str) => str);
            const { container } = render(<CreateEventModal show={true} onHide={mockOnHide} />);

            // Count tags before
            const tagBadgesBefore = container.querySelectorAll('.badge.bg-primary');
            const tagInput = screen.getByPlaceholderText('Type a tag and press Enter to add');
            fireEvent.keyDown(tagInput, { key: 'Enter' });
            // Count tags after
            const tagBadgesAfter = container.querySelectorAll('.badge.bg-primary');
            expect(tagBadgesAfter.length).toBe(tagBadgesBefore.length);
        });

        it('allows removing tags by clicking X', async () => {
            mockDefaultNameCleanup.mockImplementation((str) => str);
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const tagInput = screen.getByPlaceholderText('Type a tag and press Enter to add');
            fireEvent.change(tagInput, { target: { value: 'important' } });
            fireEvent.keyDown(tagInput, { key: 'Enter' });

            expect(screen.getByText('important')).toBeInTheDocument();

            const removeButton = screen.getByText('×');
            await userEvent.click(removeButton);

            expect(screen.queryByText('important')).not.toBeInTheDocument();
        });

        it('trims whitespace from tags', async () => {
            mockDefaultNameCleanup.mockImplementation((str) => str);
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const tagInput = screen.getByPlaceholderText('Type a tag and press Enter to add');
            fireEvent.change(tagInput, { target: { value: '  important tag  ' } });
            fireEvent.keyDown(tagInput, { key: 'Enter' });

            expect(screen.getByText('important tag')).toBeInTheDocument();
        });
    });

    describe('Form Validation', () => {
        it('disables submit button when name is empty', () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const submitButton = screen.getByRole('button', { name: /create event/i });
            expect(submitButton).toBeDisabled();
        });

        it('disables submit button when category is "All"', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event' } });

            const submitButton = screen.getByRole('button', { name: /create event/i });
            expect(submitButton).toBeDisabled();
        });

        it('enables submit button when form is valid', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event' } });

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            const submitButton = screen.getByRole('button', { name: /create event/i });
            expect(submitButton).not.toBeDisabled();
        });
    });

    describe('Prefill Logic', () => {
        it('prefills form when prefill suggestion is available', async () => {
            mockGetPrefillFromLineItems.mockReturnValue({
                name: 'Suggested Name',
                category: 'Dining'
            });

            // First render with show=false to trigger prefill
            const { rerender } = render(<CreateEventModal show={false} onHide={mockOnHide} />);

            // Then render with show=true
            rerender(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByDisplayValue('Suggested Name')).toBeInTheDocument();
            const categorySelect = screen.getByRole('combobox');
            expect(categorySelect).toHaveTextContent('Dining');
        });

        it('uses cleaned description when no prefill suggestion', async () => {
            mockGetPrefillFromLineItems.mockReturnValue(null);
            mockDefaultNameCleanup.mockReturnValue('Cleaned Description');

            // First render with show=false to trigger prefill
            const { rerender } = render(<CreateEventModal show={false} onHide={mockOnHide} />);

            // Then render with show=true
            rerender(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByDisplayValue('Cleaned Description')).toBeInTheDocument();
        });

        it('clears form when no line items are selected', async () => {
            mockUseLineItems.mockReturnValue([]);

            // First render with show=false to trigger prefill
            const { rerender } = render(<CreateEventModal show={false} onHide={mockOnHide} />);

            // Then render with show=true
            rerender(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getAllByDisplayValue('')[0]).toBeInTheDocument(); // Name input
            const categorySelect = screen.getByRole('combobox');
            expect(categorySelect).toHaveTextContent('Select a category'); // Category select placeholder
        });
    });

    describe('Event Creation', () => {
        it('creates event successfully', async () => {
            mockDefaultNameCleanup.mockImplementation((str) => str);
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event' } });

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            const dateInput = screen.getByLabelText('Override Date (optional)');
            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });

            // Add a tag
            const tagInput = screen.getByPlaceholderText('Type a tag and press Enter to add');
            fireEvent.change(tagInput, { target: { value: 'important' } });
            fireEvent.keyDown(tagInput, { key: 'Enter' });

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create event/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/events'),
                    {
                        name: 'Test Event',
                        category: 'Dining',
                        date: '2024-01-15',
                        line_items: ['1', '2'],
                        is_duplicate_transaction: false,
                        tags: ['important']
                    }
                );
            });
        });

        it('handles duplicate transaction in event creation', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event' } });

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            // Check duplicate transaction
            const checkbox = screen.getByRole('checkbox');
            await userEvent.click(checkbox);

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create event/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/events'),
                    expect.objectContaining({
                        is_duplicate_transaction: true
                    })
                );
            });
        });

        it('removes line items after successful event creation', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event' } });

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create event/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                expect(mockDispatch).toHaveBeenCalledWith({
                    type: 'remove_line_items',
                    lineItemIds: ['1', '2']
                });
            });
        });

        it('shows toast after successful event creation', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event' } });

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create event/i });
            await userEvent.click(submitButton);

            await waitFor(() => {
                const { toast } = require('sonner');
                expect(toast.success).toHaveBeenCalledWith('Created Event', {
                    description: 'Test Event',
                    duration: 3500,
                });
            });
        });

        it('handles API error gracefully', async () => {
            const { toast } = require('sonner');
            mockAxiosInstance.post.mockRejectedValue(new Error('API Error'));

            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event' } });

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            // Submit form
            const submitButton = screen.getByRole('button', { name: /create event/i });
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
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const closeButton = screen.getByRole('button', { name: /close/i });
            await userEvent.click(closeButton);

            expect(mockOnHide).toHaveBeenCalled();
        });

        it('calls onHide when cancel button is clicked', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await userEvent.click(cancelButton);

            expect(mockOnHide).toHaveBeenCalled();
        });

        it('resets form when modal is closed', async () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            // Fill out form
            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            fireEvent.change(nameInput, { target: { value: 'Test Event' } });

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            const dateInput = screen.getByLabelText('Override Date (optional)');
            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });

            // Add a tag
            const tagInput = screen.getByPlaceholderText('Type a tag and press Enter to add');
            fireEvent.change(tagInput, { target: { value: 'important' } });
            fireEvent.keyDown(tagInput, { key: 'Enter' });

            // Close modal
            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await userEvent.click(cancelButton);

            // Reopen modal
            const { rerender } = render(<CreateEventModal show={false} onHide={mockOnHide} />);
            rerender(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getAllByDisplayValue('')[0]).toBeInTheDocument(); // Name input
            const categorySelectReset = screen.getByRole('combobox');
            expect(categorySelectReset).toHaveTextContent('All'); // Category select default value
            expect(screen.queryByText('important')).not.toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('has proper modal structure', () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText('New Event Details')).toBeInTheDocument();
        });

        it('has proper form labels', () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByText('Event Name')).toBeInTheDocument();
            expect(screen.getByText('Category')).toBeInTheDocument();
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByText('Override Date (optional)')).toBeInTheDocument();
            expect(screen.getByText('Duplicate Transaction')).toBeInTheDocument();
        });

        it('has proper button labels', () => {
            render(<CreateEventModal show={true} onHide={mockOnHide} />);

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
        });
    });

    describe('Form State Management', () => {
        it('updates form fields on user input', async () => {
            await act(async () => {
                render(<CreateEventModal show={true} onHide={mockOnHide} />);
            });

            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            const dateInput = screen.getByLabelText('Override Date (optional)');

            fireEvent.change(nameInput, { target: { value: 'new@example.com' } });
            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });

            expect(nameInput).toHaveValue('new@example.com');
            expect(dateInput).toHaveValue('2024-01-15');
        });

        it('clears form fields after successful submission', async () => {
            mockAxiosInstance.post.mockResolvedValueOnce({ data: { name: 'Test Event', success: true } });

            await act(async () => {
                render(<CreateEventModal show={true} onHide={mockOnHide} />);
            });

            const nameInput = screen.getAllByDisplayValue('')[0]; // First input is name
            const dateInput = screen.getByLabelText('Override Date (optional)');
            const submitButton = screen.getByRole('button', { name: /create event/i });

            fireEvent.change(nameInput, { target: { value: 'Test Event' } });
            fireEvent.change(dateInput, { target: { value: '2024-01-15' } });

            const categorySelect = screen.getByRole('combobox');
            await userEvent.click(categorySelect);
            await userEvent.click(screen.getByRole('option', { name: 'Dining' }));

            await act(async () => {
                await userEvent.click(submitButton);
            });

            await waitFor(() => {
                expect(nameInput).toHaveValue('');
                expect(dateInput).toHaveValue('');
            });
        });
    });
}); 