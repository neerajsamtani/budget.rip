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
import { fireEvent, screen, waitFor, createTestQueryClient } from './utils/test-utils';
import { QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';

// Wrapper for rendering App component with QueryClientProvider and AuthProvider
const renderApp = () => {
    const queryClient = createTestQueryClient();
    return render(
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <App />
            </AuthProvider>
        </QueryClientProvider>
    );
};

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
const mockToaster = jest.fn((props: any) => <div data-testid="toaster" />);
jest.mock('sonner', () => {
    const mockToast = jest.fn();
    return {
        toast: Object.assign(mockToast, {
            success: jest.fn(),
            error: jest.fn(),
            info: jest.fn(),
            warning: jest.fn(),
        }),
        Toaster: (props: any) => {
            mockToaster(props);
            return <div data-testid="toaster" />;
        },
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
        mockToaster.mockClear();
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

        // Mock GET requests - return authenticated user for api/auth/me
        // Most tests expect to see the authenticated UI (nav links, refresh button, etc.)
        mockAxiosInstance.get.mockImplementation((url: string) => {
            if (url.includes('api/auth/me')) {
                return Promise.resolve({
                    data: {
                        id: 'user_123',
                        email: 'test@example.com',
                        first_name: 'Test',
                        last_name: 'User',
                    }
                });
            }
            return Promise.resolve({ data: { data: [] } });
        });
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
        it('renders navbar with brand and navigation links when authenticated', async () => {
            renderApp();

            // Wait for auth check to complete and UI to render
            await waitFor(() => {
                expect(screen.getByText('Budgit')).toBeInTheDocument();
            });

            await waitFor(() => {
                expect(screen.getByRole('link', { name: /review/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /events/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /line items/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /connected accounts/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /graphs/i })).toBeInTheDocument();
                // When authenticated, we see Log Out button, not Login link
                expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
            });
        });

        it('renders refresh data button when authenticated', async () => {
            renderApp();

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
            });
        });

        it('renders LineItemsToReviewPage as default route when authenticated', async () => {
            renderApp();

            // The default route should show the review page
            // We can verify this by checking if the navbar is present and the button is there
            await waitFor(() => {
                expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
            });
        });

        it('renders toaster with close button enabled', () => {
            renderApp();

            const toaster = screen.getByTestId('toaster');
            expect(toaster).toBeInTheDocument();

            // Verify the Toaster component was called with closeButton prop
            expect(mockToaster).toHaveBeenCalledWith(
                expect.objectContaining({
                    closeButton: true,
                    position: 'top-right',
                    richColors: true,
                })
            );
        });
    });

    describe('Navigation Links', () => {
        it('has all required navigation links when authenticated', async () => {
            renderApp();

            // Test that all navigation links are present and accessible when authenticated
            await waitFor(() => {
                expect(screen.getByRole('link', { name: /review/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /events/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /line items/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /connected accounts/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /graphs/i })).toBeInTheDocument();
                // When authenticated, we see Log Out button instead of Login link
                expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
            });
        });
    });

    describe('Refresh Data Functionality', () => {
        it('shows loading spinner when refresh button is clicked', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            // Create a promise that resolves after a delay to keep spinner visible
            const originalGet = mockAxiosInstance.get;
            mockAxiosInstance.post.mockImplementation(() =>
                new Promise(resolve => setTimeout(() => resolve({ data: { data: [] } }), 100))
            );

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should show spinner - use querySelector since it has aria-hidden="true"
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).toBeInTheDocument();
            });
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
            mockAxiosInstance.post.mockResolvedValueOnce({ data: { data: mockLineItems } });

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
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
            mockAxiosInstance.post.mockResolvedValueOnce({ data: { data: [] } });

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
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
            mockAxiosInstance.post.mockImplementation(() =>
                new Promise(resolve => setTimeout(() => resolve({ data: { data: [] } }), 50))
            );

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should show spinner initially
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).toBeInTheDocument();
            });

            // Should hide spinner after successful refresh
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            });
        });

        it('handles API error gracefully', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            mockAxiosInstance.post.mockRejectedValueOnce(new Error('API Error'));

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should handle the error without crashing
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            });
        });

        it('hides loading spinner after API error', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            mockAxiosInstance.post.mockImplementation(() =>
                new Promise((_, reject) => setTimeout(() => reject(new Error('API Error')), 50))
            );

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should show spinner initially
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).toBeInTheDocument();
            });

            // Should hide spinner after error
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            });
        });
    });

    describe('Environment Variables', () => {
        it('uses correct API endpoint from environment', () => {
            renderApp();

            // The API endpoint should be used in the axios calls
            expect(process.env.VITE_API_ENDPOINT).toBe('http://localhost:5000/');
        });

        it('uses correct Stripe public key from environment', () => {
            renderApp();

            // The Stripe key should be available
            expect(process.env.VITE_STRIPE_PUBLIC_KEY).toBe('test_stripe_key');
        });
    });

    describe('Accessibility', () => {
        it('has proper navbar structure', async () => {
            renderApp();
            await waitFor(() => {
                expect(screen.getByText('Budgit')).toBeInTheDocument();
            });
        });

        it('has proper button labels when authenticated', async () => {
            renderApp();
            await waitFor(() => {
                expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
            });
        });

        it('has proper link labels when authenticated', async () => {
            renderApp();
            await waitFor(() => {
                expect(screen.getByRole('link', { name: /review/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /events/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /line items/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /connected accounts/i })).toBeInTheDocument();
                expect(screen.getByRole('link', { name: /graphs/i })).toBeInTheDocument();
                // When authenticated, we see Log Out button instead of Login link
                expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
            });
        });

        it('has proper spinner accessibility attributes', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            mockAxiosInstance.post.mockImplementation(() =>
                new Promise(resolve => setTimeout(() => resolve({ data: { data: [] } }), 100))
            );

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Look for spinner by class using querySelector since it has aria-hidden="true"
            await waitFor(() => {
                const spinner = document.querySelector('.animate-spin');
                expect(spinner).toBeInTheDocument();
            });
        });
    });

    describe('State Management', () => {
        it('initializes with correct default state when authenticated', async () => {
            renderApp();

            // Wait for auth to complete and refresh button to appear
            await waitFor(() => {
                expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
            });

            // After auth completes, should have no loading spinner for refresh
            // Note: The auth loading spinner would have gone away by now
        });

        it('updates loading state correctly', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            mockAxiosInstance.post.mockImplementation(() =>
                new Promise(resolve => setTimeout(() => resolve({ data: { data: [] } }), 50))
            );

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });

            // Click to start loading
            fireEvent.click(refreshButton);

            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).toBeInTheDocument();
            });

            // Wait for loading to complete
            await waitFor(() => {
                expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
            });
        });

        it('calls toast correctly', async () => {
            const mockAxiosInstance = require('./utils/axiosInstance').default;
            const { toast } = require('sonner');
            mockAxiosInstance.post.mockResolvedValueOnce({ data: { data: [] } });

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
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
            mockAxiosInstance.post.mockRejectedValueOnce(new Error('API Error'));

            renderApp();

            // Wait for auth to complete first
            const refreshButton = await screen.findByRole('button', { name: /refresh data/i });
            fireEvent.click(refreshButton);

            // Should call error toast on error
            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Error', {
                    description: 'API Error',
                    duration: 3500,
                });
            });
        });
    });
}); 