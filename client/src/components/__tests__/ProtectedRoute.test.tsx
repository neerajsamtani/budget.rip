import { act } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';

// Mock axios - must be before imports that use it
jest.mock('../../utils/axiosInstance', () => ({
    __esModule: true,
    default: {
        get: jest.fn(),
        post: jest.fn(),
    },
}));

import axiosInstance from '../../utils/axiosInstance';
const mockGet = axiosInstance.get as jest.Mock;

import { ProtectedRoute, PublicOnlyRoute } from '../ProtectedRoute';
import { AuthProvider } from '../../contexts/AuthContext';

const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false },
    },
});

const renderWithProviders = (
    ui: React.ReactElement,
    { initialEntries = ['/'] } = {}
) => {
    const queryClient = createTestQueryClient();
    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={initialEntries}>
                <AuthProvider>
                    {ui}
                </AuthProvider>
            </MemoryRouter>
        </QueryClientProvider>
    );
};

describe('ProtectedRoute', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('children are rendered when user is authenticated', async () => {
        mockGet.mockResolvedValue({
            data: {
                id: 'user_123',
                email: 'test@example.com',
                first_name: 'Test',
                last_name: 'User',
            },
        });

        await act(async () => {
            renderWithProviders(
                <Routes>
                    <Route path="/" element={
                        <ProtectedRoute>
                            <div>Protected Content</div>
                        </ProtectedRoute>
                    } />
                </Routes>
            );
        });

        await waitFor(() => {
            expect(screen.getByText('Protected Content')).toBeInTheDocument();
        });
    });

    it('user is redirected to /login when not authenticated', async () => {
        mockGet.mockRejectedValue({ response: { status: 401 } });

        await act(async () => {
            renderWithProviders(
                <Routes>
                    <Route path="/" element={
                        <ProtectedRoute>
                            <div>Protected Content</div>
                        </ProtectedRoute>
                    } />
                    <Route path="/login" element={<div>Login Page</div>} />
                </Routes>
            );
        });

        await waitFor(() => {
            expect(screen.getByText('Login Page')).toBeInTheDocument();
            expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
        });
    });
});

describe('PublicOnlyRoute', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('children are rendered when user is not authenticated', async () => {
        mockGet.mockRejectedValue({ response: { status: 401 } });

        await act(async () => {
            renderWithProviders(
                <Routes>
                    <Route path="/" element={
                        <PublicOnlyRoute>
                            <div>Login Form</div>
                        </PublicOnlyRoute>
                    } />
                </Routes>
            );
        });

        await waitFor(() => {
            expect(screen.getByText('Login Form')).toBeInTheDocument();
        });
    });

    it('user is redirected to home when authenticated', async () => {
        mockGet.mockResolvedValue({
            data: {
                id: 'user_123',
                email: 'test@example.com',
                first_name: 'Test',
                last_name: 'User',
            },
        });

        await act(async () => {
            renderWithProviders(
                <Routes>
                    <Route path="/login" element={
                        <PublicOnlyRoute>
                            <div>Login Form</div>
                        </PublicOnlyRoute>
                    } />
                    <Route path="/" element={<div>Home Page</div>} />
                </Routes>,
                { initialEntries: ['/login'] }
            );
        });

        await waitFor(() => {
            expect(screen.getByText('Home Page')).toBeInTheDocument();
            expect(screen.queryByText('Login Form')).not.toBeInTheDocument();
        });
    });
});
