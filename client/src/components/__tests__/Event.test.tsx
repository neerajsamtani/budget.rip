import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import Event, { EventInterface } from '../Event';

// Mock EventDetailsModal component
jest.mock('../EventDetailsModal', () => {
    return function MockEventDetailsModal({ show, onHide }: { show: boolean; onHide: () => void }) {
        return show ? <div data-testid="event-details-modal">Event Details Modal</div> : null;
    };
});

const mockEvent: EventInterface = {
    _id: '1',
    name: 'Test Event',
    category: 'Entertainment',
    amount: 150.00,
    date: 1640995200, // Jan 1, 2022
    line_items: ['1', '2', '3'],
    tags: ['fun', 'social']
};

const mockLineItems = [
    {
        _id: '1',
        id: '1',
        date: 1640995200,
        payment_method: 'credit_card',
        description: 'Movie tickets',
        responsible_party: 'Cinema',
        amount: 50.00,
        isSelected: false,
    },
    {
        _id: '2',
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
        it('renders event data correctly', () => {
            render(
                <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
            );

            expect(screen.getByText('Test Event')).toBeInTheDocument();
            expect(screen.getByText('Entertainment')).toBeInTheDocument();
            expect(screen.getByText('$150.00')).toBeInTheDocument();
            expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
        });

        it('renders tags when present', () => {
            render(
                <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
            );

            expect(screen.getByText('fun')).toBeInTheDocument();
            expect(screen.getByText('social')).toBeInTheDocument();
        });

        it('does not render tags when not present', () => {
            const eventWithoutTags = { ...mockEvent, tags: undefined };
            render(
                <table><tbody><tr><Event event={eventWithoutTags} /></tr></tbody></table>
            );

            expect(screen.queryByText('fun')).not.toBeInTheDocument();
            expect(screen.queryByText('social')).not.toBeInTheDocument();
        });

        it('renders empty tags array correctly', () => {
            const eventWithEmptyTags = { ...mockEvent, tags: [] };
            render(
                <table><tbody><tr><Event event={eventWithEmptyTags} /></tr></tbody></table>
            );

            expect(screen.queryByText('fun')).not.toBeInTheDocument();
            expect(screen.queryByText('social')).not.toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('shows event details modal when Details button is clicked', async () => {
            render(
                <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
            );

            const detailsButton = screen.getByRole('button', { name: /details/i });
            await userEvent.click(detailsButton);

            await waitFor(() => {
                expect(screen.getByTestId('event-details-modal')).toBeInTheDocument();
            });
        });

        it('fetches line items when Details button is clicked', async () => {
            render(
                <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
            );

            const detailsButton = screen.getByRole('button', { name: /details/i });
            await userEvent.click(detailsButton);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining(`api/events/${mockEvent._id}/line_items_for_event`)
                );
            });
        });

        it('handles API error gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

            render(
                <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
            );

            const detailsButton = screen.getByRole('button', { name: /details/i });
            await userEvent.click(detailsButton);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });

            consoleSpy.mockRestore();
        });
    });

    describe('Date Formatting', () => {
        it('formats date correctly for different timestamps', () => {
            const eventWithDifferentDate = { ...mockEvent, date: 1640995200 }; // Jan 1, 2022
            render(
                <table><tbody><tr><Event event={eventWithDifferentDate} /></tr></tbody></table>
            );

            expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('has accessible button with proper label', () => {
            render(
                <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
            );

            const detailsButton = screen.getByRole('button', { name: /details/i });
            expect(detailsButton).toBeInTheDocument();
        });
    });
}); 