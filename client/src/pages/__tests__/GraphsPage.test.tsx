import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import GraphsPage from '../GraphsPage';

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

// Mock recharts to avoid rendering actual SVG charts in jsdom
jest.mock('recharts', () => {
    const Original = jest.requireActual('recharts');
    return {
        ...Original,
        ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
        BarChart: ({ children, ...props }: any) => <div data-testid="bar-chart" {...props}>{children}</div>,
        LineChart: ({ children, ...props }: any) => <div data-testid="line-chart" {...props}>{children}</div>,
        Bar: () => null,
        Line: () => null,
        XAxis: () => null,
        YAxis: () => null,
        CartesianGrid: () => null,
        Tooltip: () => null,
        Cell: () => null,
    };
});

const mockBreakdownData = {
    'Dining': [
        { amount: 150.50, date: '1-2024' },
        { amount: 200.75, date: '2-2024' },
    ],
    'Shopping': [
        { amount: 300.00, date: '1-2024' },
        { amount: 150.00, date: '2-2024' },
    ],
    'Entertainment': [
        { amount: 50.00, date: '1-2025' },
        { amount: 100.00, date: '2-2025' },
    ],
};

const mockCategories = [
    { id: '1', name: 'Dining' },
    { id: '2', name: 'Shopping' },
    { id: '3', name: 'Entertainment' },
];

const mockEvents = [
    { id: '1', name: 'Birthday Dinner', category: 'Dining', amount: 250, date: 1704067200, line_items: [] },
    { id: '2', name: 'New Laptop', category: 'Shopping', amount: 1200, date: 1706745600, line_items: [] },
    { id: '3', name: 'Concert', category: 'Entertainment', amount: 150, date: 1709424000, line_items: [] },
];

describe('GraphsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url === 'api/monthly_breakdown') {
                return Promise.resolve({ data: mockBreakdownData });
            }
            if (url === 'api/categories') {
                return Promise.resolve({ data: { data: mockCategories } });
            }
            if (url === 'api/events') {
                return Promise.resolve({ data: { data: mockEvents } });
            }
            return Promise.resolve({ data: {} });
        });
    });

    it('monthly breakdown data is fetched on mount', async () => {
        render(<GraphsPage />);

        await waitFor(() => {
            expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/monthly_breakdown');
        });
    });

    it('chart sections are rendered when data loads', async () => {
        render(<GraphsPage />);

        await waitFor(() => {
            expect(screen.getByText('Monthly Spending by Category')).toBeInTheDocument();
            expect(screen.getByText('Cumulative Spending (Year over Year)')).toBeInTheDocument();
        });
    });

    it('loading spinner shown while data loads', () => {
        mockAxiosInstance.get.mockImplementation(() => new Promise(() => { }));

        const { container } = render(<GraphsPage />);

        const spinner = container.querySelector('.animate-spin');
        expect(spinner).toBeInTheDocument();
    });

    it('error message shown when API fails', async () => {
        mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

        render(<GraphsPage />);

        await waitFor(() => {
            expect(screen.getByText(/Error loading data/i)).toBeInTheDocument();
        });
    });

    it('events are fetched for selected year', async () => {
        render(<GraphsPage />);

        await waitFor(() => {
            expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                'api/events',
                expect.objectContaining({
                    params: expect.objectContaining({
                        start_time: expect.any(Number),
                        end_time: expect.any(Number),
                    }),
                })
            );
        });
    });

    it('does not make unnecessary API calls on re-render', async () => {
        const { rerender } = render(<GraphsPage />);

        await waitFor(() => {
            expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/monthly_breakdown');
        });

        const callCount = mockAxiosInstance.get.mock.calls.length;
        rerender(<GraphsPage />);

        // No additional calls
        expect(mockAxiosInstance.get).toHaveBeenCalledTimes(callCount);
    });

    it('handles empty breakdown data', async () => {
        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url === 'api/monthly_breakdown') {
                return Promise.resolve({ data: {} });
            }
            if (url === 'api/categories') {
                return Promise.resolve({ data: { data: [] } });
            }
            if (url === 'api/events') {
                return Promise.resolve({ data: { data: [] } });
            }
            return Promise.resolve({ data: {} });
        });

        render(<GraphsPage />);

        await waitFor(() => {
            expect(screen.getByText('Monthly Spending by Category')).toBeInTheDocument();
        });
    });

    it('handles single category data', async () => {
        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url === 'api/monthly_breakdown') {
                return Promise.resolve({
                    data: { 'Dining': [{ amount: 100, date: '1-2026' }] },
                });
            }
            if (url === 'api/categories') {
                return Promise.resolve({ data: { data: [{ id: '1', name: 'Dining' }] } });
            }
            if (url === 'api/events') {
                return Promise.resolve({ data: { data: [] } });
            }
            return Promise.resolve({ data: {} });
        });

        render(<GraphsPage />);

        await waitFor(() => {
            expect(screen.getByText('Monthly Spending by Category')).toBeInTheDocument();
        });
    });

    it('handles special characters in category names', async () => {
        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url === 'api/monthly_breakdown') {
                return Promise.resolve({
                    data: {
                        'Food & Drink': [{ amount: 100, date: '1-2026' }],
                        'Self-Care': [{ amount: 50, date: '1-2026' }],
                    },
                });
            }
            if (url === 'api/categories') {
                return Promise.resolve({ data: { data: [] } });
            }
            if (url === 'api/events') {
                return Promise.resolve({ data: { data: [] } });
            }
            return Promise.resolve({ data: {} });
        });

        render(<GraphsPage />);

        await waitFor(() => {
            expect(screen.getByText('Monthly Spending by Category')).toBeInTheDocument();
        });
    });

    it('handles many categories without errors', async () => {
        const manyCategories: Record<string, Array<{ amount: number; date: string }>> = {};
        for (let i = 0; i < 20; i++) {
            manyCategories[`Category${i}`] = [
                { amount: 100 + i, date: '1-2026' },
                { amount: 200 + i, date: '2-2026' },
            ];
        }

        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url === 'api/monthly_breakdown') {
                return Promise.resolve({ data: manyCategories });
            }
            if (url === 'api/categories') {
                return Promise.resolve({ data: { data: [] } });
            }
            if (url === 'api/events') {
                return Promise.resolve({ data: { data: [] } });
            }
            return Promise.resolve({ data: {} });
        });

        render(<GraphsPage />);

        await waitFor(() => {
            expect(screen.getByText('Monthly Spending by Category')).toBeInTheDocument();
        });
    });
});
