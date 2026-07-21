import { act } from '@testing-library/react';
import React from 'react';
import { mockAxiosInstance, render, screen } from '../../utils/test-utils';
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
        window.history.pushState({}, '', '/events');
        mockAxiosInstance.get.mockResolvedValue({ data: { data: mockLineItems } });
    });

    describe('Rendering', () => {
        it('event data is displayed correctly', async () => {
            await act(async () => {
                render(
                    <table><tbody><Event event={mockEvent} /></tbody></table>
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
                    <table><tbody><Event event={mockEvent} /></tbody></table>
                );
            });

            expect(screen.getByText('fun')).toBeInTheDocument();
            expect(screen.getByText('social')).toBeInTheDocument();
        });

        it('tags are not displayed when not present', async () => {
            const eventWithoutTags = { ...mockEvent, tags: undefined };
            await act(async () => {
                render(
                    <table><tbody><Event event={eventWithoutTags} /></tbody></table>
                );
            });

            expect(screen.queryByText('fun')).not.toBeInTheDocument();
            expect(screen.queryByText('social')).not.toBeInTheDocument();
        });

        it('empty tags array is handled correctly', async () => {
            const eventWithEmptyTags = { ...mockEvent, tags: [] };
            await act(async () => {
                render(
                    <table><tbody><Event event={eventWithEmptyTags} /></tbody></table>
                );
            });

            expect(screen.queryByText('fun')).not.toBeInTheDocument();
            expect(screen.queryByText('social')).not.toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('details link points to the event detail page', async () => {
            await act(async () => {
                render(
                    <table><tbody><Event event={mockEvent} /></tbody></table>
                );
            });

            expect(screen.getByRole('link', { name: /view details/i })).toHaveAttribute('href', '/events/1');
        });

        it('details link preserves the list query string', async () => {
            window.history.pushState({}, '', '/events?month=January&tag=fun');

            await act(async () => {
                render(
                    <table><tbody><Event event={mockEvent} /></tbody></table>
                );
            });

            expect(screen.getByRole('link', { name: /view details/i })).toHaveAttribute('href', '/events/1?month=January&tag=fun');
        });

        it('does not fetch line items from the list row', async () => {
            await act(async () => {
                render(
                    <table><tbody><Event event={mockEvent} /></tbody></table>
                );
            });

            expect(mockAxiosInstance.get).not.toHaveBeenCalled();
        });
    });

    describe('Date Formatting', () => {
        it('date is formatted correctly for different timestamps', async () => {
            const eventWithDifferentDate = { ...mockEvent, date: 1640995200 }; // Jan 1, 2022
            await act(async () => {
                render(
                    <table><tbody><Event event={eventWithDifferentDate} /></tbody></table>
                );
            });

            expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('details link has accessible label', async () => {
            await act(async () => {
                render(
                    <table><tbody><Event event={mockEvent} /></tbody></table>
                );
            });

            expect(screen.getByRole('link', { name: /view details/i })).toBeInTheDocument();
        });
    });
});
