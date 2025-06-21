import { render, RenderOptions } from '@testing-library/react';
import React, { ReactElement } from 'react';
import { BrowserRouter } from 'react-router-dom';

// Mock axios instance for API calls
jest.mock('./axiosInstance', () => ({
    axiosInstance: {
        get: jest.fn(),
        post: jest.fn(),
        put: jest.fn(),
        delete: jest.fn(),
    },
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