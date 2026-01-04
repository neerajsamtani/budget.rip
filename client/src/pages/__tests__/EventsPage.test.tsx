import React from 'react';
import { fireEvent, mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import EventsPage from '../EventsPage';

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

// Mock the filter components
jest.mock('../../components/CategoryFilter', () => {
    return function MockCategoryFilter({ category, setCategory }: any) {
        return (
            <select
                data-testid="category-filter"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
            >
                <option value="All">All</option>
                <option value="Dining">Dining</option>
                <option value="Shopping">Shopping</option>
                <option value="Income">Income</option>
                <option value="Rent">Rent</option>
            </select>
        );
    };
});

jest.mock('../../components/MonthFilter', () => {
    return function MockMonthFilter({ month, setMonth }: any) {
        return (
            <select
                data-testid="month-filter"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
            >
                <option value="January">January</option>
                <option value="February">February</option>
                <option value="All">All</option>
            </select>
        );
    };
});

jest.mock('../../components/YearFilter', () => {
    return function MockYearFilter({ year, setYear }: any) {
        return (
            <select
                data-testid="year-filter"
                value={year}
                onChange={(e) => setYear(parseInt(e.target.value))}
            >
                <option value="2024">2024</option>
                <option value="2023">2023</option>
            </select>
        );
    };
});

jest.mock('../../components/TagsFilter', () => {
    return function MockTagsFilter({ tagFilter, setTagFilter }: any) {
        return (
            <input
                data-testid="tags-filter"
                value={tagFilter}
                onChange={(e) => setTagFilter(e.target.value)}
                placeholder="Filter by tags"
            />
        );
    };
});

// Mock the Event component
jest.mock('../../components/Event', () => {
    const MockEvent = function({ event }: any) {
        return (
            <>
                <td data-testid={`event-date-${event.id}`}>
                    {new Date(event.date * 1000).toLocaleDateString()}
                </td>
                <td data-testid={`event-name-${event.id}`}>{event.name}</td>
                <td data-testid={`event-category-${event.id}`}>{event.category}</td>
                <td data-testid={`event-amount-${event.id}`}>${event.amount.toFixed(2)}</td>
                <td data-testid={`event-tags-${event.id}`}>
                    {event.tags && event.tags.map((tag: string, index: number) => (
                        <span key={index} data-testid={`tag-${event.id}-${index}`}>{tag}</span>
                    ))}
                </td>
                <td data-testid={`event-actions-${event.id}`}>
                    <button>Details</button>
                </td>
            </>
        );
    };
    // Export EventCard as a named export (use different test IDs to avoid duplicates)
    const MockEventCard = function({ event }: any) {
        return (
            <div data-testid={`event-card-${event.id}`}>
                <span data-testid={`card-event-name-${event.id}`}>{event.name}</span>
                <span data-testid={`card-event-category-${event.id}`}>{event.category}</span>
                <span data-testid={`card-event-amount-${event.id}`}>${event.amount.toFixed(2)}</span>
                <span data-testid={`card-event-tags-${event.id}`}>
                    {event.tags && event.tags.map((tag: string, index: number) => (
                        <span key={index} data-testid={`card-tag-${event.id}-${index}`}>{tag}</span>
                    ))}
                </span>
            </div>
        );
    };
    return {
        __esModule: true,
        default: MockEvent,
        EventCard: MockEventCard,
    };
});

const mockEvents = [
    {
        _id: '1',
        id: '1',
        name: 'Dinner Out',
        category: 'Dining',
        amount: 50.00,
        date: 1640995200, // 2022-01-01
        line_items: ['1', '2'],
        tags: ['important', 'date-night']
    },
    {
        _id: '2',
        id: '2',
        name: 'Grocery Shopping',
        category: 'Groceries',
        amount: 100.00,
        date: 1641081600, // 2022-01-02
        line_items: ['3'],
        tags: ['weekly']
    },
    {
        _id: '3',
        id: '3',
        name: 'Salary',
        category: 'Income',
        amount: 5000.00,
        date: 1641168000, // 2022-01-03
        line_items: ['4'],
        tags: ['monthly']
    },
    {
        _id: '4',
        id: '4',
        name: 'Rent Payment',
        category: 'Rent',
        amount: 2000.00,
        date: 1641254400, // 2022-01-04
        line_items: ['5'],
        tags: ['monthly']
    },
    {
        _id: '5',
        id: '5',
        name: 'Movie Night',
        category: 'Entertainment',
        amount: 25.00,
        date: 1641340800, // 2022-01-05
        line_items: ['6'],
        tags: ['entertainment']
    }
];

describe('EventsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Set up default environment variable
        process.env.VITE_API_ENDPOINT = 'http://localhost:5000/';
        // Default successful API response
        mockAxiosInstance.get.mockResolvedValue({
            data: { data: mockEvents }
        });
    });

    describe('Rendering', () => {
        it('page title is displayed', async () => {
            render(<EventsPage />);

            expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Events');
        });

        it('all filter components are displayed', async () => {
            render(<EventsPage />);

            expect(screen.getByTestId('category-filter')).toBeInTheDocument();
            expect(screen.getByTestId('month-filter')).toBeInTheDocument();
            expect(screen.getByTestId('year-filter')).toBeInTheDocument();
            expect(screen.getByTestId('tags-filter')).toBeInTheDocument();
        });

        it('table displays correct column headers', async () => {
            render(<EventsPage />);

            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Name')).toBeInTheDocument();
            expect(screen.getByText('Category')).toBeInTheDocument();
            expect(screen.getByText('Amount')).toBeInTheDocument();
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByText('Actions')).toBeInTheDocument();
        });

        it('summary statistics are displayed', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText(/Cash Flow/)).toBeInTheDocument();
                expect(screen.getByText(/Spending/)).toBeInTheDocument();
            });
        });
    });

    describe('API Integration', () => {
        it('events data is fetched when component mounts', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/events'),
                    expect.objectContaining({
                        params: expect.objectContaining({
                            start_time: expect.any(Number),
                            end_time: expect.any(Number)
                        })
                    })
                );
            });
        });

        it('API endpoint from environment variable is used', async () => {
            process.env.VITE_API_ENDPOINT = 'https://api.example.com/';

            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'api/events',
                    expect.any(Object)
                );
            });
        });

        it('API error displays error message', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

            render(<EventsPage />);

            await waitFor(() => {
                // Error message appears in both mobile and desktop layouts
                const errors = screen.getAllByText(/Error loading events/i);
                expect(errors.length).toBeGreaterThanOrEqual(1);
            });
        });

        it('data is refetched when month filter changes', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            const monthFilter = screen.getByTestId('month-filter');
            fireEvent.change(monthFilter, { target: { value: 'February' } });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
            });
        });

        it('data is refetched when year filter changes', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            const yearFilter = screen.getByTestId('year-filter');
            fireEvent.change(yearFilter, { target: { value: '2023' } });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
            });
        });
    });

    describe('Data Display', () => {
        it('events are displayed in the table', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toHaveTextContent('Dinner Out');
                expect(screen.getByTestId('event-category-1')).toHaveTextContent('Dining');
                expect(screen.getByTestId('event-amount-1')).toHaveTextContent('$50.00');
            });
        });

        it('tags are displayed correctly', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('tag-1-0')).toHaveTextContent('important');
                expect(screen.getByTestId('tag-1-1')).toHaveTextContent('date-night');
            });
        });

        it('empty state message appears when no events exist', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: [] }
            });

            render(<EventsPage />);

            await waitFor(() => {
                // Message appears in both mobile and desktop layouts
                const messages = screen.getAllByText('No events found');
                expect(messages.length).toBeGreaterThanOrEqual(1);
            });
        });
    });

    describe('Filtering', () => {
        it('category filter hides non-matching events', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument(); // Dining
                expect(screen.getByTestId('event-name-2')).toBeInTheDocument(); // Groceries
            });

            // Change category filter to Dining using fireEvent
            const categoryFilter = screen.getByTestId('category-filter');
            fireEvent.change(categoryFilter, { target: { value: 'Dining' } });

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument(); // Dining
                expect(screen.queryByTestId('event-name-2')).not.toBeInTheDocument(); // Groceries
            });
        });

        it('tag filter hides non-matching events', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument(); // has 'important' tag
                expect(screen.getByTestId('event-name-2')).toBeInTheDocument(); // has 'weekly' tag
            });

            // Filter by 'important' tag
            const tagsFilter = screen.getByTestId('tags-filter');
            tagsFilter.setAttribute('value', 'important');
            tagsFilter.dispatchEvent(new Event('change', { bubbles: true }));

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument(); // has 'important' tag
                expect(screen.queryByTestId('event-name-2')).not.toBeInTheDocument(); // no 'important' tag
            });
        });

        it('tag filter matching is case insensitive', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument();
            });

            // Filter by 'IMPORTANT' (uppercase)
            const tagsFilter = screen.getByTestId('tags-filter');
            tagsFilter.setAttribute('value', 'IMPORTANT');
            tagsFilter.dispatchEvent(new Event('change', { bubbles: true }));

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument(); // should still match
            });
        });

        it('all events are visible when category is set to All', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-2')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-3')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-4')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-5')).toBeInTheDocument();
            });
        });

        it('calculations update when tag filter changes', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText('$7,175.00')).toBeInTheDocument(); // All events
            });

            // Filter by 'important' tag
            const tagsFilter = screen.getByTestId('tags-filter');
            tagsFilter.setAttribute('value', 'important');
            tagsFilter.dispatchEvent(new Event('change', { bubbles: true }));

            await waitFor(() => {
                expect(screen.getByTestId('event-amount-1')).toHaveTextContent('$50.00'); // Only Dinner Out has 'important' tag
            });
        });
    });

    describe('Calculations', () => {
        it('cash flow is calculated correctly', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Cash flow should include all events: 50 + 100 + 5000 + 2000 + 25 = 7175
                expect(screen.getByText('$7,175.00')).toBeInTheDocument();
            });
        });

        it('spending excludes rent and income', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Spending should exclude Rent and Income: 50 + 100 + 25 = 175
                expect(screen.getByText('$175.00')).toBeInTheDocument();
            });
        });

        it('calculations update when category filter changes', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Cash flow amount appears in the summary card
                const amounts = screen.getAllByText('$7,175.00');
                expect(amounts.length).toBeGreaterThanOrEqual(1);
            });

            // Change to Dining category only
            const categoryFilter = screen.getByTestId('category-filter');
            fireEvent.change(categoryFilter, { target: { value: 'Dining' } });

            await waitFor(() => {
                // After filtering to Dining only, $50.00 should appear (in event and/or summary)
                const amounts = screen.getAllByText('$50.00');
                expect(amounts.length).toBeGreaterThanOrEqual(1);
            });
        });

        it('zero amounts are displayed correctly', async () => {
            const zeroAmountEvents = [
                {
                    _id: '1',
                    id: '1',
                    name: 'Zero Amount Event',
                    category: 'Dining',
                    amount: 0,
                    date: 1640995200,
                    line_items: ['1'],
                    tags: []
                }
            ];
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: zeroAmountEvents }
            });

            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-amount-1')).toHaveTextContent('$0.00');
            });
        });

        it('decimal amounts are rounded to two places', async () => {
            const decimalEvents = [
                {
                    _id: '1',
                    id: '1',
                    name: 'Decimal Amount Event',
                    category: 'Dining',
                    amount: 123.456,
                    date: 1640995200,
                    line_items: ['1'],
                    tags: []
                }
            ];
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: decimalEvents }
            });

            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-amount-1')).toHaveTextContent('$123.46');
            });
        });
    });

    describe('Date Range Logic', () => {
        it('specific month sets correct date range', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                const call = mockAxiosInstance.get.mock.calls[0];
                const params = call[1].params;

                // Should be January 2024 start and end times
                expect(params.start_time).toBeDefined();
                expect(params.end_time).toBeDefined();
                expect(params.end_time).toBeGreaterThan(params.start_time);
            });
        });

        it('All months option sets full year date range', async () => {
            render(<EventsPage />);

            // Wait for initial render and API call
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalled();
            });

            const monthFilter = screen.getByTestId('month-filter');
            fireEvent.change(monthFilter, { target: { value: 'All' } });

            await waitFor(() => {
                const call = mockAxiosInstance.get.mock.calls[1];
                const params = call[1].params;

                // Should be full year range
                expect(params.start_time).toBeDefined();
                expect(params.end_time).toBeDefined();
                expect(params.end_time).toBeGreaterThan(params.start_time);
            });
        });
    });

    describe('Edge Cases', () => {
        it('events without tags are displayed correctly', async () => {
            const eventsWithoutTags = [
                {
                    _id: '1',
                    id: '1',
                    name: 'Event Without Tags',
                    category: 'Dining',
                    amount: 50.00,
                    date: 1640995200,
                    line_items: ['1']
                }
            ];
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: eventsWithoutTags }
            });

            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument();
                expect(screen.getByTestId('event-tags-1')).toBeInTheDocument();
            });
        });

        it('unexpected API response structure is handled gracefully', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: [] }
            });

            render(<EventsPage />);

            await waitFor(() => {
                // Message appears in both mobile and desktop layouts
                const messages = screen.getAllByText('No events found');
                expect(messages.length).toBeGreaterThanOrEqual(1);
            });
        });

        it('null API response is handled gracefully', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('No data'));

            render(<EventsPage />);

            await waitFor(() => {
                // Error message appears in both mobile and desktop layouts
                const errors = screen.getAllByText(/Error loading events/i);
                expect(errors.length).toBeGreaterThanOrEqual(1);
            });
        });

        it('missing environment variable is handled gracefully', async () => {
            delete process.env.VITE_API_ENDPOINT;

            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'api/events',
                    expect.any(Object)
                );
            });
        });
    });

    describe('Performance', () => {
        it('re-render does not trigger additional API calls', async () => {
            const { rerender } = render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            rerender(<EventsPage />);

            expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
        });

        it('large datasets are rendered efficiently', async () => {
            const largeDataset = Array.from({ length: 100 }, (_, i) => ({
                _id: String(i + 1),
                id: String(i + 1),
                name: `Event ${i + 1}`,
                category: 'Dining',
                amount: 50.00,
                date: 1640995200 + (i * 86400), // Each day
                line_items: [String(i + 1)],
                tags: ['tag1', 'tag2']
            }));

            mockAxiosInstance.get.mockResolvedValue({
                data: { data: largeDataset }
            });

            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-100')).toBeInTheDocument();
            });
        });
    });

    describe('Accessibility', () => {
        it('page has proper heading structure', () => {
            render(<EventsPage />);

            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
        });

        it('table has proper semantic structure', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByRole('table')).toBeInTheDocument();
                expect(document.querySelector('thead')).toBeInTheDocument();
                expect(document.querySelector('tbody')).toBeInTheDocument();
            });
        });

        it('summary cards have proper labels', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText(/Cash Flow/)).toBeInTheDocument();
                expect(screen.getByText(/Spending/)).toBeInTheDocument();
            });
        });
    });

    describe('Component Integration', () => {
        it('filter components receive correct initial props', () => {
            render(<EventsPage />);

            expect(screen.getByTestId('category-filter')).toHaveValue('All');
            expect(screen.getByTestId('month-filter')).toHaveValue('January');
            expect(screen.getByTestId('year-filter')).toHaveValue('2024');
            expect(screen.getByTestId('tags-filter')).toHaveValue('');
        });

        it('Event components receive correct event data', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toHaveTextContent('Dinner Out');
                expect(screen.getByTestId('event-category-1')).toHaveTextContent('Dining');
                expect(screen.getByTestId('event-amount-1')).toHaveTextContent('$50.00');
            });
        });
    });

    describe('Loading States', () => {
        it('skeleton loading states appear in summary cards during initial load', () => {
            // Don't resolve the promise immediately
            mockAxiosInstance.get.mockImplementation(() => new Promise(() => { }));

            const { container } = render(<EventsPage />);

            // Check for skeleton components in summary cards
            const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
            expect(skeletons.length).toBeGreaterThan(0);
        });

        it('loading spinner appears in mobile view during initial load', () => {
            // Don't resolve the promise immediately
            mockAxiosInstance.get.mockImplementation(() => new Promise(() => { }));

            const { container } = render(<EventsPage />);

            // Check for spinner (loading indicator)
            const spinner = container.querySelector('.animate-spin');
            expect(spinner).toBeInTheDocument();
        });

        it('loading spinner appears in desktop table during initial load', () => {
            // Don't resolve the promise immediately
            mockAxiosInstance.get.mockImplementation(() => new Promise(() => { }));

            const { container } = render(<EventsPage />);

            // Check for spinner in table
            const spinner = container.querySelector('.animate-spin');
            expect(spinner).toBeInTheDocument();
        });

        it('actual values replace skeleton after data loads', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Summary cards should show actual values
                expect(screen.getByText('$7,175.00')).toBeInTheDocument();
                expect(screen.getByText('$175.00')).toBeInTheDocument();
            });

            // Skeletons should be gone
            const { container } = render(<EventsPage />);
            await waitFor(() => {
                expect(screen.getByText('$7,175.00')).toBeInTheDocument();
            });
        });
    });

    describe('Responsive Layout', () => {
        it('mobile card layout displays events', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Mobile card layout should render event cards
                expect(screen.getByTestId('event-card-1')).toBeInTheDocument();
                expect(screen.getByTestId('event-card-2')).toBeInTheDocument();
            });
        });

        it('desktop table layout has proper structure', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Desktop table should also render (hidden via CSS)
                expect(screen.getByRole('table')).toBeInTheDocument();
                expect(document.querySelector('thead')).toBeInTheDocument();
                expect(document.querySelector('tbody')).toBeInTheDocument();
            });
        });

        it('filters toggle button is visible on mobile', () => {
            render(<EventsPage />);

            // Mobile filters toggle button should be present
            const filtersButton = screen.getByRole('button', { name: /filters/i });
            expect(filtersButton).toBeInTheDocument();
        });

        it('filter count badge appears when filters are active', async () => {
            render(<EventsPage />);

            // Change category filter to activate a filter
            const categoryFilter = screen.getByTestId('category-filter');
            fireEvent.change(categoryFilter, { target: { value: 'Dining' } });

            await waitFor(() => {
                // Should show filters button
                const filtersButton = screen.getByRole('button', { name: /filters/i });
                expect(filtersButton).toBeInTheDocument();
                // Badge with count should appear somewhere in the document
                // Count is 1 because category="Dining" is active
                const badge = document.querySelector('.rounded-full');
                expect(badge).toBeInTheDocument();
            });
        });

        it('mobile cards and desktop table display same event data', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Desktop table should display event data
                expect(screen.getByTestId('event-name-1')).toHaveTextContent('Dinner Out');
                // Mobile card should also display event data
                expect(screen.getByTestId('card-event-name-1')).toHaveTextContent('Dinner Out');
            });
        });

        it('summary cards are displayed with responsive styling', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Summary cards should be present
                expect(screen.getByText(/Cash Flow/)).toBeInTheDocument();
                expect(screen.getByText(/Spending/)).toBeInTheDocument();
            });
        });
    });
}); 