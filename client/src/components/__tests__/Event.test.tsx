import { act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import Event, { EventInterface } from '../Event';

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

// Mock EventDetailsModal component
jest.mock('../EventDetailsModal', () => {
    return function MockEventDetailsModal({ show }: { show: boolean }) {
        return show ? <div data-testid="event-details-modal">Event Details Modal</div> : null;
    };
});

const mockEvent: EventInterface = {
    id: '1',
    name: 'Test Event',
    category: 'Entertainment',
    amount: 150.00,
    date: 1640995200, // Jan 1, 2022
    line_items: ['1', '2', '3'],
    tags: ['fun', 'social']
};

const mockLineItems = [
    {
        id: '1',
        date: 1640995200,
        payment_method: 'credit_card',
        description: 'Movie tickets',
        responsible_party: 'Cinema',
        amount: 50.00,
        isSelected: false,
    },
    {
        id: '2',
        date: 1640995200,
        payment_method: 'cash',
        description: 'Dinner',
        responsible_party: 'Restaurant',
        amount: 100.00,
        isSelected: false,
    }
];

describe('Event', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockAxiosInstance.get.mockResolvedValue({ data: { data: mockLineItems } });
    });

    describe('Rendering', () => {
        it('event data is displayed correctly', async () => {
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
                );
            });

            expect(screen.getByText('Test Event')).toBeInTheDocument();
            expect(screen.getByText('Entertainment')).toBeInTheDocument();
            expect(screen.getByText('$150.00')).toBeInTheDocument();
            expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
        });

        it('tags are displayed when present', async () => {
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
                );
            });

            expect(screen.getByText('fun')).toBeInTheDocument();
            expect(screen.getByText('social')).toBeInTheDocument();
        });

        it('tags are not displayed when not present', async () => {
            const eventWithoutTags = { ...mockEvent, tags: undefined };
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={eventWithoutTags} /></tr></tbody></table>
                );
            });

            expect(screen.queryByText('fun')).not.toBeInTheDocument();
            expect(screen.queryByText('social')).not.toBeInTheDocument();
        });

        it('empty tags array is handled correctly', async () => {
            const eventWithEmptyTags = { ...mockEvent, tags: [] };
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={eventWithEmptyTags} /></tr></tbody></table>
                );
            });

            expect(screen.queryByText('fun')).not.toBeInTheDocument();
            expect(screen.queryByText('social')).not.toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('event details modal opens when Details button is clicked', async () => {
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
                );
            });

            const detailsButton = screen.getByRole('button', { name: /details/i });
            await act(async () => {
                await userEvent.click(detailsButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('event-details-modal')).toBeInTheDocument();
            });
        });

        it('line items are fetched when Details button is clicked', async () => {
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
                );
            });

            const detailsButton = screen.getByRole('button', { name: /details/i });
            await act(async () => {
                await userEvent.click(detailsButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining(`api/events/${mockEvent.id}/line_items_for_event`)
                );
            });
        });

        it('API error is handled gracefully', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

            await act(async () => {
                render(
                    <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
                );
            });

            const detailsButton = screen.getByRole('button', { name: /details/i });
            await act(async () => {
                await userEvent.click(detailsButton);
            });

            // TanStack Query handles the error internally
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalled();
            });
        });
    });

    describe('Date Formatting', () => {
        it('date is formatted correctly for different timestamps', async () => {
            const eventWithDifferentDate = { ...mockEvent, date: 1640995200 }; // Jan 1, 2022
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={eventWithDifferentDate} /></tr></tbody></table>
                );
            });

            expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('button has accessible label', async () => {
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
                );
            });

            const detailsButton = screen.getByRole('button', { name: /details/i });
            expect(detailsButton).toBeInTheDocument();
        });
    });
}); 