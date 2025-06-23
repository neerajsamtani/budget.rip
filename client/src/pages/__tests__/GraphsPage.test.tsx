import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import GraphsPage from '../GraphsPage';

// Mock the Plot component from react-plotly.js
jest.mock('react-plotly.js', () => {
    return function MockPlot({ data, layout }: any) {
        return (
            <div data-testid="plot-component">
                <div data-testid="plot-data" data-plot-data={JSON.stringify(data)}>
                    {data.map((trace: any, index: number) => (
                        <div key={index} data-testid={`plot-trace-${index}`}>
                            <span data-testid={`trace-name-${index}`}>{trace.name}</span>
                            <span data-testid={`trace-type-${index}`}>{trace.type}</span>
                            <span data-testid={`trace-x-${index}`}>{trace.x.join(',')}</span>
                            <span data-testid={`trace-y-${index}`}>{trace.y.join(',')}</span>
                        </div>
                    ))}
                </div>
                <div data-testid="plot-layout" data-plot-layout={JSON.stringify(layout)}>
                    <span data-testid="layout-barmode">{layout.barmode}</span>
                    <span data-testid="layout-width">{layout.width}</span>
                    <span data-testid="layout-height">{layout.height}</span>
                </div>
            </div>
        );
    };
});

const mockCategorizedData = {
    'Dining': [
        { amount: 150.50, date: '2024-01-01' },
        { amount: 200.75, date: '2024-01-02' },
        { amount: 75.25, date: '2024-01-03' }
    ],
    'Shopping': [
        { amount: 300.00, date: '2024-01-01' },
        { amount: 150.00, date: '2024-01-02' }
    ],
    'Entertainment': [
        { amount: 50.00, date: '2024-01-01' },
        { amount: 100.00, date: '2024-01-03' }
    ]
};

describe('GraphsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Set up default environment variable
        process.env.REACT_APP_API_ENDPOINT = 'http://localhost:5000/';
        // Default successful API response
        mockAxiosInstance.get.mockResolvedValue({
            data: mockCategorizedData
        });
    });

    describe('Rendering', () => {
        it('renders the plot component', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });
        });

        it('renders plot with correct number of traces', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-trace-0')).toBeInTheDocument();
                expect(screen.getByTestId('plot-trace-1')).toBeInTheDocument();
                expect(screen.getByTestId('plot-trace-2')).toBeInTheDocument();
            });
        });

        it('renders plot with correct layout properties', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('layout-barmode')).toHaveTextContent('relative');
                expect(screen.getByTestId('layout-width')).toHaveTextContent('1000');
                expect(screen.getByTestId('layout-height')).toHaveTextContent('600');
            });
        });
    });

    describe('API Integration', () => {
        it('fetches monthly breakdown data on component mount', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'http://localhost:5000/api/monthly_breakdown',
                    { params: {} }
                );
            });
        });

        it('uses correct API endpoint from environment variable', async () => {
            process.env.REACT_APP_API_ENDPOINT = 'https://api.example.com/';

            render(<GraphsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'https://api.example.com/api/monthly_breakdown',
                    { params: {} }
                );
            });
        });

        it('handles API errors gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.get.mockRejectedValue(new Error('API Error'));

            render(<GraphsPage />);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });

            consoleSpy.mockRestore();
        });

        it('handles empty API response', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: {}
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });
        });

        it('handles null API response', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: null
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });
        });
    });

    describe('Data Transformation', () => {
        it('transforms categorized data into plot traces correctly', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                // Check Dining trace
                expect(screen.getByTestId('trace-name-0')).toHaveTextContent('Dining');
                expect(screen.getByTestId('trace-type-0')).toHaveTextContent('bar');
                expect(screen.getByTestId('trace-x-0')).toHaveTextContent('2024-01-01,2024-01-02,2024-01-03');
                expect(screen.getByTestId('trace-y-0')).toHaveTextContent('150.5,200.75,75.25');

                // Check Shopping trace
                expect(screen.getByTestId('trace-name-1')).toHaveTextContent('Shopping');
                expect(screen.getByTestId('trace-type-1')).toHaveTextContent('bar');
                expect(screen.getByTestId('trace-x-1')).toHaveTextContent('2024-01-01,2024-01-02');
                expect(screen.getByTestId('trace-y-1')).toHaveTextContent('300,150');

                // Check Entertainment trace
                expect(screen.getByTestId('trace-name-2')).toHaveTextContent('Entertainment');
                expect(screen.getByTestId('trace-type-2')).toHaveTextContent('bar');
                expect(screen.getByTestId('trace-x-2')).toHaveTextContent('2024-01-01,2024-01-03');
                expect(screen.getByTestId('trace-y-2')).toHaveTextContent('50,100');
            });
        });

        it('handles single category data', async () => {
            const singleCategoryData = {
                'Dining': [
                    { amount: 150.50, date: '2024-01-01' },
                    { amount: 200.75, date: '2024-01-02' }
                ]
            };
            mockAxiosInstance.get.mockResolvedValue({
                data: singleCategoryData
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('trace-name-0')).toHaveTextContent('Dining');
                expect(screen.getByTestId('trace-x-0')).toHaveTextContent('2024-01-01,2024-01-02');
                expect(screen.getByTestId('trace-y-0')).toHaveTextContent('150.5,200.75');
            });
        });

        it('handles empty category data', async () => {
            const emptyCategoryData = {
                'Empty Category': []
            };
            mockAxiosInstance.get.mockResolvedValue({
                data: emptyCategoryData
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('trace-name-0')).toHaveTextContent('Empty Category');
                expect(screen.getByTestId('trace-x-0')).toHaveTextContent('');
                expect(screen.getByTestId('trace-y-0')).toHaveTextContent('');
            });
        });

        it('handles categories with single data point', async () => {
            const singlePointData = {
                'Single Point': [
                    { amount: 100.00, date: '2024-01-01' }
                ]
            };
            mockAxiosInstance.get.mockResolvedValue({
                data: singlePointData
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('trace-name-0')).toHaveTextContent('Single Point');
                expect(screen.getByTestId('trace-x-0')).toHaveTextContent('2024-01-01');
                expect(screen.getByTestId('trace-y-0')).toHaveTextContent('100');
            });
        });
    });

    describe('Layout Configuration', () => {
        it('sets correct layout properties', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                const layoutElement = screen.getByTestId('plot-layout');
                const layoutData = JSON.parse(layoutElement.getAttribute('data-plot-layout') || '{}');

                expect(layoutData.barmode).toBe('relative');
                expect(layoutData.xaxis.title).toBe('Date');
                expect(layoutData.yaxis.title).toBe('Amount');
                expect(layoutData.width).toBe(1000);
                expect(layoutData.height).toBe(600);
            });
        });

        it('maintains consistent layout structure', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('layout-barmode')).toBeInTheDocument();
                expect(screen.getByTestId('layout-width')).toBeInTheDocument();
                expect(screen.getByTestId('layout-height')).toBeInTheDocument();
            });
        });
    });

    describe('Data Handling', () => {
        it('handles zero amounts correctly', async () => {
            const zeroAmountData = {
                'Zero Amount': [
                    { amount: 0, date: '2024-01-01' },
                    { amount: 0, date: '2024-01-02' }
                ]
            };
            mockAxiosInstance.get.mockResolvedValue({
                data: zeroAmountData
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('trace-y-0')).toHaveTextContent('0,0');
            });
        });

        it('handles decimal amounts correctly', async () => {
            const decimalData = {
                'Decimal Amounts': [
                    { amount: 123.456, date: '2024-01-01' },
                    { amount: 789.012, date: '2024-01-02' }
                ]
            };
            mockAxiosInstance.get.mockResolvedValue({
                data: decimalData
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('trace-y-0')).toHaveTextContent('123.456,789.012');
            });
        });

        it('handles large amounts correctly', async () => {
            const largeAmountData = {
                'Large Amounts': [
                    { amount: 999999.99, date: '2024-01-01' },
                    { amount: 1000000.00, date: '2024-01-02' }
                ]
            };
            mockAxiosInstance.get.mockResolvedValue({
                data: largeAmountData
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('trace-y-0')).toHaveTextContent('999999.99,1000000');
            });
        });

        it('handles special characters in category names', async () => {
            const specialCharData = {
                'Category & Name': [
                    { amount: 100.00, date: '2024-01-01' }
                ],
                'Category-Name': [
                    { amount: 200.00, date: '2024-01-01' }
                ]
            };
            mockAxiosInstance.get.mockResolvedValue({
                data: specialCharData
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('trace-name-0')).toHaveTextContent('Category & Name');
                expect(screen.getByTestId('trace-name-1')).toHaveTextContent('Category-Name');
            });
        });
    });

    describe('Loading States', () => {
        it('shows plot component during initial load', () => {
            // Don't resolve the promise immediately
            mockAxiosInstance.get.mockImplementation(() => new Promise(() => { }));

            render(<GraphsPage />);

            expect(screen.getByTestId('plot-component')).toBeInTheDocument();
        });

        it('updates plot when data loads', async () => {
            // Initially show empty data
            mockAxiosInstance.get.mockResolvedValue({
                data: {}
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });

            // Clear the mock and set up new response
            mockAxiosInstance.get.mockClear();
            mockAxiosInstance.get.mockResolvedValue({
                data: mockCategorizedData
            });

            // Re-render to trigger new data load
            const { rerender } = render(<GraphsPage />);
            rerender(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('trace-name-0')).toHaveTextContent('Dining');
            });
        });
    });

    describe('Error Scenarios', () => {
        it('handles API response with unexpected structure', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: { unexpected: 'structure' }
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });
        });

        it('handles API response with null data field', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: null
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });
        });

        it('handles API response with undefined data field', async () => {
            mockAxiosInstance.get.mockResolvedValue({
                data: undefined
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });
        });

        it('handles network timeout gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.get.mockRejectedValue(new Error('Network timeout'));

            render(<GraphsPage />);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });

            consoleSpy.mockRestore();
        });
    });

    describe('Performance', () => {
        it('does not make unnecessary API calls on re-render', async () => {
            const { rerender } = render(<GraphsPage />);

            // Wait for initial load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            // Re-render without changes
            rerender(<GraphsPage />);

            // Should not make additional API calls
            expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
        });

        it('handles large datasets efficiently', async () => {
            const largeDataset = {};
            // Create a large dataset with many categories
            for (let i = 0; i < 50; i++) {
                largeDataset[`Category${i}`] = [
                    { amount: 100 + i, date: '2024-01-01' },
                    { amount: 200 + i, date: '2024-01-02' }
                ];
            }
            mockAxiosInstance.get.mockResolvedValue({
                data: largeDataset
            });

            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });
        });
    });

    describe('Accessibility', () => {
        it('renders plot component with proper structure', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-component')).toBeInTheDocument();
            });
        });

        it('maintains plot data accessibility', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                expect(screen.getByTestId('plot-data')).toBeInTheDocument();
                expect(screen.getByTestId('plot-layout')).toBeInTheDocument();
            });
        });
    });

    describe('Component Integration', () => {
        it('passes correct props to Plot component', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                const plotData = screen.getByTestId('plot-data');
                const data = JSON.parse(plotData.getAttribute('data-plot-data') || '[]');

                expect(data).toHaveLength(3); // Three categories
                expect(data[0]).toHaveProperty('name', 'Dining');
                expect(data[0]).toHaveProperty('type', 'bar');
                expect(data[0]).toHaveProperty('x');
                expect(data[0]).toHaveProperty('y');
            });
        });

        it('maintains data integrity through transformations', async () => {
            render(<GraphsPage />);

            await waitFor(() => {
                // Verify that the original data structure is preserved in the plot
                const plotData = screen.getByTestId('plot-data');
                const data = JSON.parse(plotData.getAttribute('data-plot-data') || '[]');

                // Check that all categories are present
                const categoryNames = data.map((trace: any) => trace.name);
                expect(categoryNames).toContain('Dining');
                expect(categoryNames).toContain('Shopping');
                expect(categoryNames).toContain('Entertainment');
            });
        });
    });

    describe('Edge Cases', () => {
        it('handles environment variable changes', async () => {
            // Change environment variable
            process.env.REACT_APP_API_ENDPOINT = 'https://new-api.example.com/';

            render(<GraphsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'https://new-api.example.com/api/monthly_breakdown',
                    { params: {} }
                );
            });
        });

        it('handles missing environment variable', async () => {
            // Remove environment variable
            delete process.env.REACT_APP_API_ENDPOINT;

            render(<GraphsPage />);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    'undefinedapi/monthly_breakdown',
                    { params: {} }
                );
            });
        });

        it('handles rapid re-renders', async () => {
            const { rerender } = render(<GraphsPage />);

            // Wait for initial load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
            });

            // Rapid re-renders
            rerender(<GraphsPage />);
            rerender(<GraphsPage />);
            rerender(<GraphsPage />);

            // Should still only have one API call
            expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
        });
    });
}); 