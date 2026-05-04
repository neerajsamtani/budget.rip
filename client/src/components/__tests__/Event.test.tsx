import { act } from '@testing-library/react';
import React from 'react';
import { mockAxiosInstance, render, screen } from '../../utils/test-utils';
import Event, { EventInterface } from '../Event';

const mockEvent: EventInterface = {
    id: '1',
    name: 'Test Event',
    category: 'Entertainment',
    amount: 150.00,
    date: 1640995200, // Jan 1, 2022
    line_items: ['1', '2', '3'],
    tags: ['fun', 'social']
};

describe('Event', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockAxiosInstance.get.mockResolvedValue({ data: { data: [] } });
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

    describe('Navigation', () => {
        it('view details link points to the event detail page', async () => {
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
                );
            });

            const detailsLink = screen.getByRole('link', { name: /view details/i });
            expect(detailsLink).toBeInTheDocument();
            expect(detailsLink.getAttribute('href')).toBe('/events/1');
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
        it('view details link has accessible label', async () => {
            await act(async () => {
                render(
                    <table><tbody><tr><Event event={mockEvent} /></tr></tbody></table>
                );
            });

            const detailsLink = screen.getByRole('link', { name: /view details/i });
            expect(detailsLink).toBeInTheDocument();
        });
    });
});
