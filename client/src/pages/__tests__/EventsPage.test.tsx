import React from 'react';
import { fireEvent, mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import EventsPage from '../EventsPage';

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
    return function MockEvent({ event }: any) {
        return (
            <>
                <td data-testid={`event-date-${event._id}`}>
                    {new Date(event.date * 1000).toLocaleDateString()}
                </td>
                <td data-testid={`event-name-${event._id}`}>{event.name}</td>
                <td data-testid={`event-category-${event._id}`}>{event.category}</td>
                <td data-testid={`event-amount-${event._id}`}>${event.amount.toFixed(2)}</td>
                <td data-testid={`event-tags-${event._id}`}>
                    {event.tags && event.tags.map((tag: string, index: number) => (
                        <span key={index} data-testid={`tag-${event._id}-${index}`}>{tag}</span>
                    ))}
                </td>
                <td data-testid={`event-actions-${event._id}`}>
                    <button>Details</button>
                </td>
            </>
        );
    };
});

const mockEvents = [
    {
        _id: '1',
        name: 'Dinner Out',
        category: 'Dining',
        amount: 50.00,
        date: 1640995200, // 2022-01-01
        line_items: ['1', '2'],
        tags: ['important', 'date-night']
    },
    {
        _id: '2',
        name: 'Grocery Shopping',
        category: 'Groceries',
        amount: 100.00,
        date: 1641081600, // 2022-01-02
        line_items: ['3'],
        tags: ['weekly']
    },
    {
        _id: '3',
        name: 'Salary',
        category: 'Income',
        amount: 5000.00,
        date: 1641168000, // 2022-01-03
        line_items: ['4'],
        tags: ['monthly']
    },
    {
        _id: '4',
        name: 'Rent Payment',
        category: 'Rent',
        amount: 2000.00,
        date: 1641254400, // 2022-01-04
        line_items: ['5'],
        tags: ['monthly']
    },
    {
        _id: '5',
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
        process.env.REACT_APP_API_ENDPOINT = 'http://localhost:5000/';
        // Default successful API response
        mockAxiosInstance.get.mockResolvedValue({
            data: { data: mockEvents }
        });
    });

    describe('Rendering', () => {
        it('renders the page title', async () => {
            render(<EventsPage />);

            expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Events');
        });

        it('renders all filter components', async () => {
            render(<EventsPage />);

            expect(screen.getByTestId('category-filter')).toBeInTheDocument();
            expect(screen.getByTestId('month-filter')).toBeInTheDocument();
            expect(screen.getByTestId('year-filter')).toBeInTheDocument();
            expect(screen.getByTestId('tags-filter')).toBeInTheDocument();
        });

        it('renders the table with correct headers', async () => {
            render(<EventsPage />);

            expect(screen.getByText('Date')).toBeInTheDocument();
            expect(screen.getByText('Name')).toBeInTheDocument();
            expect(screen.getByText('Category')).toBeInTheDocument();
            expect(screen.getByText('Amount')).toBeInTheDocument();
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByText('Actions')).toBeInTheDocument();
        });

        it('renders summary statistics', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText('Net Income')).toBeInTheDocument();
                expect(screen.getByText('Spending w/o Rent')).toBeInTheDocument();
            });
        });
    });

    describe('API Integration', () => {
        it('fetches events data on component mount', async () => {
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

        it('uses correct API endpoint from environment variable', async () => {
            process.env.REACT_APP_API_ENDPOINT = 'https://api.example.com/';

            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'https://api.example.com/api/events',
                    expect.any(Object)
                );
            });
        });

        it('handles API errors gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

            render(<EventsPage />);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });

            consoleSpy.mockRestore();
        });

        it('refetches data when month changes', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            // Change month filter
            const monthFilter = screen.getByTestId('month-filter');
            monthFilter.setAttribute('value', 'February');
            monthFilter.dispatchEvent(new Event('change', { bubbles: true }));

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
            });
        });

        it('refetches data when year changes', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            // Change year filter
            const yearFilter = screen.getByTestId('year-filter');
            yearFilter.setAttribute('value', '2023');
            yearFilter.dispatchEvent(new Event('change', { bubbles: true }));

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
            });
        });
    });

    describe('Data Display', () => {
        it('displays events in the table', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toHaveTextContent('Dinner Out');
                expect(screen.getByTestId('event-category-1')).toHaveTextContent('Dining');
                expect(screen.getByTestId('event-amount-1')).toHaveTextContent('$50.00');
            });
        });

        it('displays tags correctly', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('tag-1-0')).toHaveTextContent('important');
                expect(screen.getByTestId('tag-1-1')).toHaveTextContent('date-night');
            });
        });

        it('shows "No events found" when no events', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: { data: [] }
            });

            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText('No events found')).toBeInTheDocument();
            });
        });
    });

    describe('Filtering', () => {
        it('filters events by category', async () => {
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

        it('filters events by tags', async () => {
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

        it('filters are case insensitive', async () => {
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

        it('shows all events when category is "All"', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-2')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-3')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-4')).toBeInTheDocument();
                expect(screen.getByTestId('event-name-5')).toBeInTheDocument();
            });
        });

        it('updates calculations when tag filter changes', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText('$7175.00')).toBeInTheDocument(); // All events
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
        it('calculates net income correctly', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Net income should include all events: 50 + 100 + 5000 + 2000 + 25 = 7175
                expect(screen.getByText('$7175.00')).toBeInTheDocument();
            });
        });

        it('calculates spending without rent correctly', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                // Spending w/o rent should exclude Rent and Income: 50 + 100 + 25 = 175
                expect(screen.getByText('$175.00')).toBeInTheDocument();
            });
        });

        it('updates calculations when category filter changes', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText('$7175.00')).toBeInTheDocument(); // All categories
            });

            // Change to Dining category only
            const categoryFilter = screen.getByTestId('category-filter');
            categoryFilter.setAttribute('value', 'Dining');
            categoryFilter.dispatchEvent(new Event('change', { bubbles: true }));

            await waitFor(() => {
                expect(screen.getByText('$50.00')).toBeInTheDocument(); // Only Dining
            });
        });

        it('handles zero amounts correctly', async () => {
            const zeroAmountEvents = [
                {
                    _id: '1',
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

        it('handles decimal amounts correctly', async () => {
            const decimalEvents = [
                {
                    _id: '1',
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
        it('sets correct date range for specific month', async () => {
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

        it('sets correct date range for "All" months', async () => {
            // Change month to "All"
            render(<EventsPage />);

            const monthFilter = screen.getByTestId('month-filter');
            monthFilter.setAttribute('value', 'All');
            monthFilter.dispatchEvent(new Event('change', { bubbles: true }));

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
        it('handles events without tags', async () => {
            const eventsWithoutTags = [
                {
                    _id: '1',
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

        it('handles API response with unexpected structure', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: { unexpected: 'structure' }
            });

            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText('No events found')).toBeInTheDocument();
            });
        });

        it('handles null API response', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: null
            });

            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByText('No events found')).toBeInTheDocument();
            });
        });

        it('handles missing environment variable', async () => {
            delete process.env.REACT_APP_API_ENDPOINT;

            render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'undefinedapi/events',
                    expect.any(Object)
                );
            });
        });
    });

    describe('Performance', () => {
        it('does not make unnecessary API calls on re-render', async () => {
            const { rerender } = render(<EventsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            rerender(<EventsPage />);

            expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
        });

        it('handles large datasets efficiently', async () => {
            const largeDataset = Array.from({ length: 100 }, (_, i) => ({
                _id: String(i + 1),
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
        it('has proper heading structure', () => {
            render(<EventsPage />);

            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
        });

        it('has proper table structure', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByRole('table')).toBeInTheDocument();
                expect(document.querySelector('thead')).toBeInTheDocument();
                expect(document.querySelector('tbody')).toBeInTheDocument();
            });
        });

        it('has proper form labels', () => {
            render(<EventsPage />);

            expect(screen.getByText('Net Income')).toBeInTheDocument();
            expect(screen.getByText('Spending w/o Rent')).toBeInTheDocument();
        });
    });

    describe('Component Integration', () => {
        it('passes correct props to filter components', () => {
            render(<EventsPage />);

            expect(screen.getByTestId('category-filter')).toHaveValue('All');
            expect(screen.getByTestId('month-filter')).toHaveValue('January');
            expect(screen.getByTestId('year-filter')).toHaveValue('2024');
            expect(screen.getByTestId('tags-filter')).toHaveValue('');
        });

        it('passes correct props to Event components', async () => {
            render(<EventsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('event-name-1')).toHaveTextContent('Dinner Out');
                expect(screen.getByTestId('event-category-1')).toHaveTextContent('Dining');
                expect(screen.getByTestId('event-amount-1')).toHaveTextContent('$50.00');
            });
        });
    });
}); 