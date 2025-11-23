import userEvent from '@testing-library/user-event';
import React from 'react';
import { LineItemInterface } from '../../contexts/LineItemsContext';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
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

// Mock the LineItem component
jest.mock('../LineItem', () => {
    const MockLineItem = function MockLineItem({ lineItem }: { lineItem: LineItemInterface }) {
        return (
            <tr data-testid={`line-item-${lineItem._id}`}>
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
            <div data-testid={`line-item-card-${lineItem._id}`}>
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
        _id: 'event-1',
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
            _id: 'line-1',
            id: 'line-1',
            date: 1640995200,
            payment_method: 'credit_card',
            description: 'Lunch at restaurant',
            responsible_party: 'John Doe',
            amount: 75.00,
            isSelected: false
        },
        {
            _id: 'line-2',
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
    });

    describe('Rendering', () => {
        it('renders modal when show is true', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
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
                    onHide={mockOnHide}
                />
            );

            const closeButtons = screen.getAllByRole('button', { name: /close/i });
            await userEvent.click(closeButtons[0]);

            expect(mockOnHide).toHaveBeenCalled();
        });

        it('calls onHide when close button is clicked', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    onHide={mockOnHide}
                />
            );

            const closeButtons = screen.getAllByRole('button', { name: /close/i });
            await userEvent.click(closeButtons[1]);

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
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            await waitFor(() => {
                expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
                    expect.stringContaining(`api/events/${mockEvent._id}`)
                );
            });
        });

        it('shows toast after successful deletion', async () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
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
            mockAxiosInstance.delete.mockRejectedValue(new Error('API Error'));

            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
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
            mockAxiosInstance.delete.mockRejectedValue(new Error('API Error'));

            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            // Wait a bit to ensure the promise rejection is handled
            await new Promise(resolve => setTimeout(resolve, 100));

            expect(mockOnHide).not.toHaveBeenCalled();
        });
    });

    describe('Environment Configuration', () => {
        it('uses VITE_API_ENDPOINT environment variable', async () => {
            const originalEnv = process.env.VITE_API_ENDPOINT;
            process.env.VITE_API_ENDPOINT = 'http://localhost:3000/';

            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
                    onHide={mockOnHide}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await userEvent.click(deleteButton);

            await waitFor(() => {
                expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
                    'api/events/event-1'
                );
            });

            // Restore original environment
            process.env.VITE_API_ENDPOINT = originalEnv;
        });
    });

    describe('Accessibility', () => {
        it('has proper modal structure', () => {
            render(
                <EventDetailsModal
                    show={true}
                    event={mockEvent}
                    lineItemsForEvent={mockLineItems}
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
                _id: 'event-2',
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
                    _id: 'line-3',
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
}); 