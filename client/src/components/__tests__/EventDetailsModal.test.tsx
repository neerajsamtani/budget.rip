import userEvent from '@testing-library/user-event';
import React from 'react';
import { LineItemInterface } from '../../contexts/LineItemsContext';
import { fireEvent, mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import { EventInterface } from '../Event';
import EventDetailsModal from '../EventDetailsModal';

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

// Mock the API hooks
const mockUpdateEvent = jest.fn();
const mockDeleteEvent = jest.fn();
jest.mock('../../hooks/useApi', () => ({
    ...jest.requireActual('../../hooks/useApi'),
    useDeleteEvent: () => ({
        mutate: mockDeleteEvent,
        isPending: false,
    }),
    useUpdateEvent: () => ({
        mutate: mockUpdateEvent,
        isPending: false,
    }),
    useTags: () => ({
        data: [
            { id: 'tag-1', name: 'food' },
            { id: 'tag-2', name: 'travel' },
        ],
        isLoading: false,
    }),
    useLineItems: () => ({
        data: [],
        isLoading: false,
    }),
}));

// Mock the LineItem component
jest.mock('../LineItem', () => {
    const MockLineItem = function MockLineItem({ lineItem }: { lineItem: LineItemInterface }) {
        return (
            <tr data-testid={`line-item-${lineItem.id}`}>
                <td>{new Date(lineItem.date * 1000).toLocaleDateString()}</td>
                <td>{lineItem.payment_method}</td>
                <td>{lineItem.description}</td>
                <td>{lineItem.responsible_party}</td>
                <td>${lineItem.amount.toFixed(2)}</td>
            </tr>
        );
    };
    const MockLineItemCard = function MockLineItemCard({ lineItem }: any) {
        return (
            <div data-testid={`line-item-card-${lineItem.id}`}>
                <span>{lineItem.description}</span>
                <span>${lineItem.amount.toFixed(2)}</span>
            </div>
        );
    };
    return {
        __esModule: true,
        default: MockLineItem,
        LineItemCard: MockLineItemCard,
    };
});

describe('EventDetailsModal', () => {
    const mockOnHide = jest.fn();

    const mockEvent: EventInterface = {
        id: 'event-1',
        name: 'Test Event',
        category: 'Dining',
        amount: 150.00,
        date: 1640995200, // 2022-01-01
        line_items: ['line-1', 'line-2'],
        tags: ['important', 'business']
    };

    const mockLineItems: LineItemInterface[] = [
        {
            id: 'line-1',
            date: 1640995200,
            payment_method: 'credit_card',
            description: 'Lunch at restaurant',
            responsible_party: 'John Doe',
            amount: 75.00,
            isSelected: false
        },
        {
            id: 'line-2',
            date: 1640995200,
            payment_method: 'cash',
            description: 'Dinner at cafe',
            responsible_party: 'Jane Smith',
            amount: 75.00,
            isSelected: false
        }
    ];

    beforeEach(() => {
        jest.clearAllMocks();
        mockAxiosInstance.delete.mockResolvedValue({ data: { success: true } });
        // Default mock implementation - calls onSuccess
        mockDeleteEvent.mockImplementation((_eventId, options) => {
            options?.onSuccess?.();
        });
        mockUpdateEvent.mockImplementation((_data, options) => {
            options?.onSuccess?.();
        });
    });

    describe('Rendering', () => {
        it('renders modal when show is true', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText('Test Event')).toBeInTheDocument();
            expect(screen.getByText((content, element) => {
                return element?.textContent === 'Category: Dining';
            })).toBeInTheDocument();
        });

        it('does not render modal when show is false', () => {
            render(
                <EventDetailsModal
                    show={false}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        it('renders event title with name and category', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByText('Test Event')).toBeInTheDocument();
            expect(screen.getByText((content, element) => {
                return element?.textContent === 'Category: Dining';
            })).toBeInTheDocument();
        });

        it('renders table headers', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Payment Method')).toBeInTheDocument();
            expect(screen.getByText('Description')).toBeInTheDocument();
            expect(screen.getByText('Name')).toBeInTheDocument();
            expect(screen.getByText('Amount')).toBeInTheDocument();
        });

        it('renders line items in table', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByTestId('line-item-line-1')).toBeInTheDocument();
            expect(screen.getByTestId('line-item-line-2')).toBeInTheDocument();
        });

        it('renders tags when event has tags', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByText('Tags:')).toBeInTheDocument();
            expect(screen.getByText('important')).toBeInTheDocument();
            expect(screen.getByText('business')).toBeInTheDocument();
        });

        it('does not render tags section when event has no tags', () => {
            const eventWithoutTags = { ...mockEvent, tags: undefined };

            render(
                <EventDetailsModal
                    show={true}
                    event={eventWithoutTags}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.queryByText('Tags:')).not.toBeInTheDocument();
            expect(screen.queryByText('important')).not.toBeInTheDocument();
        });

        it('does not render tags section when event has empty tags array', () => {
            const eventWithEmptyTags = { ...mockEvent, tags: [] };

            render(
                <EventDetailsModal
                    show={true}
                    event={eventWithEmptyTags}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.queryByText('Tags:')).not.toBeInTheDocument();
        });

        it('renders action buttons', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getAllByRole('button', { name: /close/i }).length).toBeGreaterThanOrEqual(1);
            expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
        });

        it('renders empty table when no line items', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={[]}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.queryByTestId(/line-item-/)).not.toBeInTheDocument();
        });
    });

    describe('Modal Interactions', () => {
        it('calls onHide when close button is clicked', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const closeButtons = screen.getAllByRole('button', { name: /close/i });
            await userEvent.click(closeButtons[0]);

            expect(mockOnHide).toHaveBeenCalled();
        });
    });

    describe('Event Deletion', () => {
        it('deletes event successfully', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            await waitFor(() => {
                expect(mockDeleteEvent).toHaveBeenCalledWith(
                    'event-1',
                    expect.any(Object)
                );
            });
        });

        it('shows toast after successful deletion', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            await waitFor(() => {
                const { toast } = require('sonner');
                expect(toast.success).toHaveBeenCalledWith('Deleted Event', {
                    description: 'Test Event',
                    duration: 3500,
                });
            });
        });

        it('calls onHide after successful deletion', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            await waitFor(() => {
                expect(mockOnHide).toHaveBeenCalled();
            });
        });


        it('handles API error gracefully', async () => {
            const { toast } = require('sonner');
            mockDeleteEvent.mockImplementation((eventId, options) => {
                options?.onError?.(new Error('API Error'));
            });

            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith("Error", {
                    description: "API Error",
                    duration: 3500,
                });
            });
        });

        it('does not call onHide when deletion fails', async () => {
            mockDeleteEvent.mockImplementation((eventId, options) => {
                options?.onError?.(new Error('API Error'));
            });

            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            // Wait a bit to ensure the error is handled
            await new Promise(resolve => setTimeout(resolve, 100));

            expect(mockOnHide).not.toHaveBeenCalled();
        });
    });

    describe('Environment Configuration', () => {
        it('calls delete mutation with event id', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            await waitFor(() => {
                expect(mockDeleteEvent).toHaveBeenCalledWith(
                    'event-1',
                    expect.any(Object)
                );
            });
        });
    });

    describe('Accessibility', () => {
        it('has proper modal structure', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText('Test Event')).toBeInTheDocument();
            expect(screen.getByText((content, element) => {
                return element?.textContent === 'Category: Dining';
            })).toBeInTheDocument();
        });

        it('has proper button labels', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getAllByRole('button', { name: /close/i }).length).toBeGreaterThanOrEqual(1);
            expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
        });

        it('has proper table structure', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByRole('table')).toBeInTheDocument();
            expect(screen.getByRole('columnheader', { name: 'Date' })).toBeInTheDocument();
            expect(screen.getByRole('columnheader', { name: 'Payment Method' })).toBeInTheDocument();
            expect(screen.getByRole('columnheader', { name: 'Description' })).toBeInTheDocument();
            expect(screen.getByRole('columnheader', { name: 'Name' })).toBeInTheDocument();
            expect(screen.getByRole('columnheader', { name: 'Amount' })).toBeInTheDocument();
        });
    });

    describe('Data Display', () => {
        it('displays line items with correct data', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            // Check that line items are rendered with their data
            expect(screen.getByTestId('line-item-line-1')).toBeInTheDocument();
            expect(screen.getByTestId('line-item-line-2')).toBeInTheDocument();
        });

        it('displays tags with correct styling', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const tagBadges = screen.getAllByText(/important|business/);
            expect(tagBadges).toHaveLength(2);

            tagBadges.forEach(badge => {
                expect(badge).toBeInTheDocument();
            });
        });

        it('handles event with different data types', () => {
            const eventWithDifferentData: EventInterface = {
                id: 'event-2',
                name: 'Another Event',
                category: 'Shopping',
                amount: 299.99,
                date: 1640995200,
                line_items: ['line-3'],
                tags: ['personal', 'urgent']
            };

            const singleLineItem: LineItemInterface[] = [
                {
                    id: 'line-3',
                    date: 1640995200,
                    payment_method: 'debit_card',
                    description: 'Online purchase',
                    responsible_party: 'Online Store',
                    amount: 299.99,
                    isSelected: false
                }
            ];

            render(
                <EventDetailsModal
                    show={true}
                    event={eventWithDifferentData}
                    lineItemsForEvent={singleLineItem}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            expect(screen.getByText('Another Event')).toBeInTheDocument();
            expect(screen.getByText((content, element) => {
                return element?.textContent === 'Category: Shopping';
            })).toBeInTheDocument();
            expect(screen.getByTestId('line-item-line-3')).toBeInTheDocument();
            expect(screen.getByText('personal')).toBeInTheDocument();
            expect(screen.getByText('urgent')).toBeInTheDocument();
        });
    });

    describe('State Management', () => {
        it('initializes notification state correctly', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            // Notification should not be shown initially
            expect(screen.queryByTestId('notification')).not.toBeInTheDocument();
        });

        it('calls toast after successful deletion', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            await waitFor(() => {
                const { toast } = require('sonner');
                expect(toast.success).toHaveBeenCalledWith('Deleted Event', {
                    description: 'Test Event',
                    duration: 3500,
                });
            });
        });
    });

    describe('Edit Mode', () => {
        beforeEach(() => {
            mockUpdateEvent.mockClear();
        });

        it('enters edit mode when Edit button is clicked', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            // Should be in view mode initially
            expect(screen.getByText('Test Event')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();

            // Click Edit button
            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Should now be in edit mode
            expect(screen.getByText('Edit Event')).toBeInTheDocument();
            expect(screen.getByLabelText(/event name/i)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
        });

        it('populates form fields with event data when entering edit mode', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Check that name field is populated
            expect(screen.getByLabelText(/event name/i)).toHaveValue('Test Event');

            // Check that tags are displayed
            expect(screen.getByText('important')).toBeInTheDocument();
            expect(screen.getByText('business')).toBeInTheDocument();
        });

        it('cancels editing and returns to view mode', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            // Enter edit mode
            await userEvent.click(screen.getByRole('button', { name: /edit/i }));
            expect(screen.getByText('Edit Event')).toBeInTheDocument();

            // Make a change
            const nameInput = screen.getByLabelText(/event name/i);
            await userEvent.clear(nameInput);
            await userEvent.type(nameInput, 'Modified Name');

            // Cancel editing
            await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

            // Should be back in view mode with original name
            expect(screen.getByText('Test Event')).toBeInTheDocument();
            expect(screen.queryByText('Edit Event')).not.toBeInTheDocument();
        });

        it('displays line items with remove buttons in edit mode', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Should show line items with descriptions
            expect(screen.getByText('Lunch at restaurant')).toBeInTheDocument();
            expect(screen.getByText('Dinner at cafe')).toBeInTheDocument();

            // Should show remove buttons
            const removeButtons = screen.getAllByRole('button', { name: /remove/i });
            expect(removeButtons.length).toBe(2);
        });

        it('removes a line item when Remove is clicked', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Should show both line items initially
            expect(screen.getByText('Lunch at restaurant')).toBeInTheDocument();
            expect(screen.getByText('Dinner at cafe')).toBeInTheDocument();
            expect(screen.getByText('Line Items (2)')).toBeInTheDocument();

            // Remove the first line item
            const removeButtons = screen.getAllByRole('button', { name: /remove/i });
            await userEvent.click(removeButtons[0]);

            // Should now show only one line item
            expect(screen.queryByText('Lunch at restaurant')).not.toBeInTheDocument();
            expect(screen.getByText('Dinner at cafe')).toBeInTheDocument();
            expect(screen.getByText('Line Items (1)')).toBeInTheDocument();
        });

        it('disables remove button when only one line item remains', async () => {
            const singleLineItem = [mockLineItems[0]];
            const singleLineItemEvent = { ...mockEvent, line_items: ['line-1'] };

            render(
                <EventDetailsModal
                    show={true}
                    event={singleLineItemEvent}
                    lineItemsForEvent={singleLineItem}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Remove button should be disabled
            const removeButton = screen.getByRole('button', { name: /remove/i });
            expect(removeButton).toBeDisabled();
        });

        it('adds a removed line item back to the event', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Remove the first line item
            const removeButtons = screen.getAllByRole('button', { name: /remove/i });
            await userEvent.click(removeButtons[0]);

            // Should now show only one line item
            expect(screen.queryByText('Lunch at restaurant')).not.toBeInTheDocument();
            expect(screen.getByText('Line Items (1)')).toBeInTheDocument();

            // The autocomplete for adding line items should now be visible
            expect(screen.getByPlaceholderText(/search for line items/i)).toBeInTheDocument();

            // Type in the autocomplete to search for the removed item
            const autocomplete = screen.getByPlaceholderText(/search for line items/i);
            await userEvent.type(autocomplete, 'Lunch');

            // Click on the matching option to add it back
            await waitFor(() => {
                expect(screen.getByText(/Lunch at restaurant/)).toBeInTheDocument();
            });
            await userEvent.click(screen.getByText(/Lunch at restaurant/));

            // Should now show both line items again
            await waitFor(() => {
                expect(screen.getByText('Line Items (2)')).toBeInTheDocument();
            });
        });

        it('displays total in edit mode', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Total should be displayed (75 + 75 = 150)
            expect(screen.getByText('Total:')).toBeInTheDocument();
            expect(screen.getByText('$150.00')).toBeInTheDocument();
        });

        // Using fireEvent instead of userEvent due to Radix dialog + JSDom incompatibility.
        // JSDom doesn't support PointerEvent which Radix needs for scroll lock cleanup,
        // causing pointer-events: none to persist on body between tests.
        // See: https://github.com/radix-ui/primitives/issues/1241
        it('updates total when duplicate transaction is checked', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            fireEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Initial total should be $150.00
            expect(screen.getByText('$150.00')).toBeInTheDocument();

            // Check duplicate transaction checkbox
            const checkbox = screen.getByRole('checkbox');
            fireEvent.click(checkbox);

            // Total should now be first item only ($75.00)
            expect(screen.getByText('$75.00')).toBeInTheDocument();
        });

        it('calls update API with correct data when saving', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Modify the name
            const nameInput = screen.getByLabelText(/event name/i);
            await userEvent.clear(nameInput);
            await userEvent.type(nameInput, 'Updated Event Name');

            // Save changes
            await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

            // Verify update was called with correct data
            expect(mockUpdateEvent).toHaveBeenCalledWith(
                expect.objectContaining({
                    eventId: 'event-1',
                    name: 'Updated Event Name',
                    category: 'Dining',
                    line_items: ['line-1', 'line-2'],
                }),
                expect.any(Object)
            );
        });

        it('disables save button when name is empty', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Clear the name
            const nameInput = screen.getByLabelText(/event name/i);
            await userEvent.clear(nameInput);

            // Save button should be disabled
            expect(screen.getByRole('button', { name: /save changes/i })).toBeDisabled();
        });

        it('removes tag when X is clicked', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    isLoadingLineItemsForEvent={false}
                    onHide={mockOnHide}
                />
            );

            await userEvent.click(screen.getByRole('button', { name: /edit/i }));

            // Both tags should be visible
            expect(screen.getByText('important')).toBeInTheDocument();
            expect(screen.getByText('business')).toBeInTheDocument();

            // Find and click the X button for the first tag
            const tagBadges = screen.getAllByText('×');
            await userEvent.click(tagBadges[0]);

            // First tag should be removed
            expect(screen.queryByText('important')).not.toBeInTheDocument();
            expect(screen.getByText('business')).toBeInTheDocument();
        });
    });
}); 