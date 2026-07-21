import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { createTestQueryClient, mockAxiosInstance } from '../../utils/test-utils';
import EventDetailPage from '../EventDetailPage';

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

const mockEvent = {
    id: 'event-1',
    name: 'Dinner Out',
    category: 'Dining',
    amount: 150,
    date: 1640995200,
    line_items: ['line-1', 'line-2'],
    tags: ['friends'],
    is_duplicate_transaction: false,
};

const mockLineItems = [
    {
        id: 'line-1',
        date: 1640995200,
        payment_method: 'Chase Card',
        description: 'Restaurant',
        responsible_party: 'Neeraj',
        amount: 75,
    },
    {
        id: 'line-2',
        date: 1640995300,
        payment_method: 'Amex',
        description: 'Dessert',
        responsible_party: 'Friend',
        amount: 75,
    },
];

const mockCategories = [
    { id: 'cat-dining', name: 'Dining' },
    { id: 'cat-travel', name: 'Travel' },
];

function LocationProbe() {
    const location = useLocation();
    return <div data-testid="location">{location.pathname}{location.search}</div>;
}

function renderEventDetail(initialEntry = '/events/event-1?month=January&category=Dining') {
    const queryClient = createTestQueryClient();
    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={[initialEntry]}>
                <Routes>
                    <Route path="/events/:eventId" element={<><EventDetailPage /><LocationProbe /></>} />
                    <Route path="/events" element={<><div>Events List</div><LocationProbe /></>} />
                </Routes>
            </MemoryRouter>
        </QueryClientProvider>
    );
}

function mockDefaultApiResponses() {
    mockAxiosInstance.get.mockImplementation((url: string) => {
        if (url === 'api/events/event-1') {
            return Promise.resolve({ data: mockEvent });
        }
        if (url === 'api/events/event-1/line_items_for_event') {
            return Promise.resolve({ data: { data: mockLineItems } });
        }
        if (url === 'api/categories') {
            return Promise.resolve({ data: { data: mockCategories } });
        }
        if (url === 'api/tags') {
            return Promise.resolve({ data: { data: [{ id: 'tag-friends', name: 'friends' }] } });
        }
        if (url === 'api/line_items') {
            return Promise.resolve({ data: { data: [] } });
        }
        return Promise.resolve({ data: { data: [] } });
    });
    mockAxiosInstance.put.mockResolvedValue({ data: { ...mockEvent, name: 'Dinner Updated' } });
    mockAxiosInstance.delete.mockResolvedValue({ data: 'Deleted Event' });
}

describe('EventDetailPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockDefaultApiResponses();
    });

    it('fetches event and linked line items', async () => {
        renderEventDetail();

        await waitFor(() => expect(screen.getByRole('heading', { name: 'Dinner Out' })).toBeInTheDocument());

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/events/event-1');
        expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/events/event-1/line_items_for_event');
        expect(screen.getAllByText('Restaurant').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Dessert').length).toBeGreaterThan(0);
    });

    it('renders the details rail from event and line item data', async () => {
        renderEventDetail();

        await waitFor(() => expect(screen.getByText('Event ID')).toBeInTheDocument());

        expect(screen.getByText('event-1')).toBeInTheDocument();
        expect(screen.getAllByText('Dining').length).toBeGreaterThan(0);
        expect(screen.getAllByText('friends').length).toBeGreaterThan(0);
        expect(screen.getByText('Chase Card, Amex')).toBeInTheDocument();
        expect(screen.getByText('Neeraj, Friend')).toBeInTheDocument();
    });

    it('shows an error state when the event cannot be loaded', async () => {
        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url === 'api/events/event-1') {
                return Promise.reject(new Error('Not found'));
            }
            return Promise.resolve({ data: { data: [] } });
        });

        renderEventDetail();

        await waitFor(() => expect(screen.getByRole('heading', { name: 'Event not found' })).toBeInTheDocument());
        expect(screen.getByRole('link', { name: /Events/ })).toHaveAttribute('href', '/events?month=January&category=Dining');
    });

    it('saves edits and stays on the detail route', async () => {
        renderEventDetail();

        await waitFor(() => expect(screen.getByRole('button', { name: /Edit/ })).toBeInTheDocument());
        await userEvent.click(screen.getByRole('button', { name: /Edit/ }));
        await userEvent.clear(screen.getByLabelText('Event Name'));
        await userEvent.type(screen.getByLabelText('Event Name'), 'Dinner Updated');
        await userEvent.click(screen.getByRole('button', { name: /Save Changes/ }));

        await waitFor(() => {
            expect(mockAxiosInstance.put).toHaveBeenCalledWith('api/events/event-1', expect.objectContaining({
                name: 'Dinner Updated',
                category: 'Dining',
                line_items: ['line-1', 'line-2'],
                tags: ['friends'],
            }));
        });
        expect(screen.getByTestId('location')).toHaveTextContent('/events/event-1?month=January&category=Dining');
    });

    it('deletes the event and navigates back to the filtered list', async () => {
        renderEventDetail();

        await waitFor(() => expect(screen.getByRole('button', { name: /Delete/ })).toBeInTheDocument());
        await userEvent.click(screen.getByRole('button', { name: /Delete/ }));

        await waitFor(() => expect(mockAxiosInstance.delete).toHaveBeenCalledWith('api/events/event-1'));
        expect(screen.getByText('Events List')).toBeInTheDocument();
        expect(screen.getByTestId('location')).toHaveTextContent('/events?month=January&category=Dining');
    });

    it('preserves list filters in the back link', async () => {
        renderEventDetail('/events/event-1?year=2024&tag=friends');

        await waitFor(() => expect(screen.getByRole('link', { name: /Events/ })).toBeInTheDocument());

        expect(screen.getByRole('link', { name: /Events/ })).toHaveAttribute('href', '/events?year=2024&tag=friends');
    });
});
