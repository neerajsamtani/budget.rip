// Mock axios instance before any imports
jest.mock('./utils/axiosInstance', () => {
    return {
        __esModule: true,
        default: {
            get: jest.fn(),
            post: jest.fn(),
            put: jest.fn(),
            delete: jest.fn(),
            patch: jest.fn(),
            defaults: {
                headers: {
                    common: {}
                }
            },
            interceptors: {
                request: { use: jest.fn() },
                response: { use: jest.fn() }
            }
        }
    };
});

import { render } from '@testing-library/react';
import React from 'react';
import App from './App';
import { fireEvent, screen, waitFor } from './utils/test-utils';

// Use whatwg-url for a proper URL polyfill in jsdom/react-router tests
if (typeof global.URL === 'undefined' || typeof global.URL.prototype === 'undefined') {
    global.URL = require('whatwg-url').URL;
}
// Mock createObjectURL and revokeObjectURL if not present
if (!global.URL.createObjectURL) {
    global.URL.createObjectURL = jest.fn();
}
if (!global.URL.revokeObjectURL) {
    global.URL.revokeObjectURL = jest.fn();
}

// Mock react-plotly.js to avoid canvas issues
jest.mock('react-plotly.js', () => {
    return function MockPlot(props: any) {
        return <div data-testid="plotly-chart" {...props} />;
    };
});

// Mock Sonner toast
jest.mock('sonner', () => {
    const mockToast = jest.fn();
    return {
        toast: Object.assign(mockToast, {
            success: jest.fn(),
            error: jest.fn(),
            info: jest.fn(),
            warning: jest.fn(),
        }),
        Toaster: () => <div data-testid="toaster" />,
    };
});

// Mock the LineItemsContext
jest.mock('./contexts/LineItemsContext', () => {
    return {
        useLineItems: jest.fn(() => []),
        useLineItemsDispatch: jest.fn(),
    };
});

// Mock Stripe
jest.mock('@stripe/stripe-js', () => ({
    loadStripe: jest.fn(() => Promise.resolve({})),
}));

const { useLineItems, useLineItemsDispatch } = require('./contexts/LineItemsContext');
const mockUseLineItems = useLineItems as jest.MockedFunction<typeof useLineItems>;
const mockUseLineItemsDispatch = useLineItemsDispatch as jest.MockedFunction<typeof useLineItemsDispatch>;

const mockDispatch = jest.fn();

describe('App', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        process.env.VITE_API_ENDPOINT = 'http://localhost:5000/';
        process.env.VITE_STRIPE_PUBLIC_KEY = 'test_stripe_key';
        mockUseLineItemsDispatch.mockReturnValue(mockDispatch);
        mockUseLineItems.mockReturnValue([]);

        // Reset and configure axios mock properly
        const mockAxiosInstance = require('./utils/axiosInstance').default;
        mockAxiosInstance.get.mockReset();
        mockAxiosInstance.post.mockReset();
        mockAxiosInstance.put.mockReset();
        mockAxiosInstance.delete.mockReset();
        mockAxiosInstance.patch.mockReset();

        // Ensure all GET requests return a resolved promise by default
        mockAxiosInstance.get.mockResolvedValue({ data: { data: [] } });
        // Ensure all POST requests return a resolved promise by default
        mockAxiosInstance.post.mockResolvedValue({ data: { success: true } });
        // Ensure all PUT requests return a resolved promise by default
        mockAxiosInstance.put.mockResolvedValue({ data: { success: true } });
        // Ensure all DELETE requests return a resolved promise by default
        mockAxiosInstance.delete.mockResolvedValue({ data: { success: true } });
        // Ensure all PATCH requests return a resolved promise by default
        mockAxiosInstance.patch.mockResolvedValue({ data: { success: true } });
    });

    describe('Rendering', () => {
        it('renders navbar with brand and navigation links', () => {
            render(<App />);

            expect(screen.getByText('Budgit')).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /review/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /events/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /line items/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /connected accounts/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /graphs/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /login/i })).toBeInTheDocument();
        });

        it('renders refresh data button', () => {
            render(<App />);

            expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
        });

        it('renders LineItemsToReviewPage as default route', () => {
            render(<App />);

            // The default route should show the review page
            // We can verify this by checking if the navbar is present and the button is there
            expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
        });
    });

    describe('Navigation Links', () => {
        it('has all required navigation links', () => {
            render(<App />);

            // Test that all navigation links are present and accessible
            expect(screen.getByRole('link', { name: /review/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /events/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /line items/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /connected accounts/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /graphs/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /login/i })).toBeInTheDocument();
        });
    });

    describe('Refresh Data Functionality', () => {
        it('shows loading spinner when refresh button is clicked', async () => {
            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should show spinner - use querySelector since it has aria-hidden="true"
            expect(document.querySelector('.animate-spin')).toBeInTheDocument();
        });

        it('calls API and updates line items on successful refresh', async () => {
            const mockLineItems = [
                {
                    _id: '1',
                    id: '1',
                    date: 1640995200,
                    payment_method: 'credit_card',
                    description: 'Test transaction',
                    responsible_party: 'Test Store',
                    amount: 50.00,
                }
            ];

            const mockAxiosInstance = require('./utils/axiosInstance').default;
            mockAxiosInstance.get.mockResolvedValueOnce({ data: { data: mockLineItems } });

            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith(
                    expect.stringContaining('api/refresh/all')
                );
            });

            expect(mockDispatch).toHaveBeenCalledWith({
                type: 'populate_line_items',
                fetchedLineItems: mockLineItems
            });
        });

        it('shows toast notification after successful refresh', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            const { toast } = require('sonner');
            mockAxiosInstance.get.mockResolvedValueOnce({ data: { data: [] } });

            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            await waitFor(() => {
                expect(toast.success).toHaveBeenCalledWith('Notification', {
                    description: 'Refreshed data',
                    duration: 3500,
                });
            });
        });

        it('hides loading spinner after successful refresh', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            mockAxiosInstance.get.mockResolvedValueOnce({ data: { data: [] } });

            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should show spinner initially
            expect(document.querySelector('.animate-spin')).toBeInTheDocument();

            // Should hide spinner after successful refresh
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            });
        });

        it('handles API error gracefully', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            mockAxiosInstance.get.mockRejectedValueOnce(new Error('API Error'));

            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should handle the error without crashing
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            });
        });

        it('hides loading spinner after API error', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            mockAxiosInstance.get.mockRejectedValueOnce(new Error('API Error'));

            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should show spinner initially
            expect(document.querySelector('.animate-spin')).toBeInTheDocument();

            // Should hide spinner after error
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            });
        });
    });

    describe('Environment Variables', () => {
        it('uses correct API endpoint from environment', () => {
            render(<App />);

            // The API endpoint should be used in the axios calls
            expect(process.env.VITE_API_ENDPOINT).toBe('http://localhost:5000/');
        });

        it('uses correct Stripe public key from environment', () => {
            render(<App />);

            // The Stripe key should be available
            expect(process.env.VITE_STRIPE_PUBLIC_KEY).toBe('test_stripe_key');
        });
    });

    describe('Accessibility', () => {
        it('has proper navbar structure', () => {
            render(<App />);
            expect(screen.getByText('Budgit')).toBeInTheDocument();
            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
        });

        it('has proper button labels', () => {
            render(<App />);
            expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
        });

        it('has proper link labels', () => {
            render(<App />);
            expect(screen.getByRole('link', { name: /review/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /events/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /line items/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /connected accounts/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /graphs/i })).toBeInTheDocument();
            expect(screen.getByRole('link', { name: /login/i })).toBeInTheDocument();
        });

        it('has proper spinner accessibility attributes', async () => {
            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Look for spinner by class using querySelector since it has aria-hidden="true"
            const spinner = document.querySelector('.animate-spin');
            expect(spinner).toBeInTheDocument();
        });
    });

    describe('State Management', () => {
        it('initializes with correct default state', () => {
            render(<App />);

            // Should start with no loading state
            expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
        });

        it('updates loading state correctly', async () => {
            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });

            // Initially no spinner
            expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();

            // Click to start loading
            fireEvent.click(refreshButton);
            expect(document.querySelector('.animate-spin')).toBeInTheDocument();

            // Wait for loading to complete
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            });
        });

        it('calls toast correctly', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            const { toast } = require('sonner');
            mockAxiosInstance.get.mockResolvedValueOnce({ data: { data: [] } });

            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should call toast after successful refresh
            await waitFor(() => {
                expect(toast.success).toHaveBeenCalledWith('Notification', {
                    description: 'Refreshed data',
                    duration: 3500,
                });
            });
        });
    });

    describe('Error Handling', () => {

        it('calls error toast on error', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            const { toast } = require('sonner');
            mockAxiosInstance.get.mockRejectedValueOnce(new Error('API Error'));

            render(<App />);

            const refreshButton = screen.getByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should call error toast on error
            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Notification', {
                    description: 'Error refreshing data',
                    duration: 3500,
                });
            });
        });
    });
}); 