import { render, RenderOptions } from '@testing-library/react';
import React, { ReactElement } from 'react';
import { BrowserRouter } from 'react-router-dom';

// Polyfill for hasPointerCapture - needed for Radix UI components in tests
if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
}

if (!Element.prototype.setPointerCapture) {
    Element.prototype.setPointerCapture = () => {};
}

if (!Element.prototype.releasePointerCapture) {
    Element.prototype.releasePointerCapture = () => {};
}

// Polyfill for scrollIntoView - needed for Radix UI Select component in tests
if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
}

// Mock axios instance for API calls - create mock without importing axios
const mockAxiosInstance = {
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
};

// Mock the axios instance module
jest.mock('../utils/axiosInstance', () => ({
    __esModule: true,
    default: mockAxiosInstance,
}));

// Custom render function that includes basic providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
    return (
        <BrowserRouter>
            {children}
        </BrowserRouter>
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