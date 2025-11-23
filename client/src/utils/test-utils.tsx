import { render, RenderOptions } from '@testing-library/react';
import React, { ReactElement } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Polyfill for hasPointerCapture - needed for Radix UI components in tests
if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
}

if (!Element.prototype.setPointerCapture) {
    Element.prototype.setPointerCapture = () => { };
}

if (!Element.prototype.releasePointerCapture) {
    Element.prototype.releasePointerCapture = () => { };
}

// Polyfill for scrollIntoView - needed for Radix UI Select component in tests
if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => { };
}

// Mock the axios instance module - must be before any imports that use it
jest.mock('../utils/axiosInstance', () => ({
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
    },
}));

// Get reference to the mocked axios instance
import axiosInstance from '../utils/axiosInstance';
const mockAxiosInstance = axiosInstance as jest.Mocked<typeof axiosInstance>;

// Create a custom query client for tests with no retries
export const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
        queries: {
            retry: false,
            gcTime: 0,
        },
        mutations: {
            retry: false,
        },
    },
});

// Custom render function that includes basic providers
// Note: AuthProvider is NOT included here to avoid extra API calls in non-auth tests
// Tests that need AuthProvider should use their own wrapper (see auth tests for examples)
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
    const queryClient = createTestQueryClient();
    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                {children}
            </BrowserRouter>
        </QueryClientProvider>
    );
};

const customRender = (
    ui: ReactElement,
    options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';

// Override render method
export { customRender as render };

// Export mock axios instance for tests
export { mockAxiosInstance };

// Mock data for tests
export const mockLineItem = {
    _id: '1',
    id: '1',
    date: 1640995200, // Unix timestamp for 2022-01-01
    payment_method: 'credit_card',
    description: 'Test transaction',
    responsible_party: 'Test Store',
    amount: 50.00,
    isSelected: false,
};

export const mockEvent = {
    _id: '1',
    id: '1',
    name: 'Test Event',
    date: 1640995200,
    description: 'Test event description',
    line_items: [],
    totalAmount: 100.00,
};

// Helper to wait for async operations
export const waitForElementToBeRemoved = (element: HTMLElement) => {
    return new Promise((resolve) => {
        const observer = new MutationObserver(() => {
            if (!document.contains(element)) {
                observer.disconnect();
                resolve(true);
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    });
}; 