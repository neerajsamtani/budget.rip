import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock axios instance
jest.mock('../../utils/axiosInstance', () => ({
    __esModule: true,
    default: {
        get: jest.fn(),
        post: jest.fn(),
    },
}));

import axiosInstance from '../../utils/axiosInstance';
const mockGet = axiosInstance.get as jest.Mock;

import { useCurrentUser, authQueryKeys } from '../useAuth';

const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false },
    },
});

const createWrapper = () => {
    const queryClient = createTestQueryClient();
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useAuth hooks', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('authQueryKeys', () => {
        it('currentUser query key has correct format', () => {
            expect(authQueryKeys.currentUser).toEqual(['currentUser']);
        });
    });

    describe('useCurrentUser', () => {
        it('user data is returned when authenticated', async () => {
            const mockUser = {
                id: 'user_123',
                email: 'test@example.com',
                first_name: 'Test',
                last_name: 'User',
            };
            mockGet.mockResolvedValue({ data: mockUser });

            const { result } = renderHook(() => useCurrentUser(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/auth/me');
            expect(result.current.data).toEqual(mockUser);
        });

        it('null is returned when not authenticated', async () => {
            mockGet.mockRejectedValue({ response: { status: 401 } });

            const { result } = renderHook(() => useCurrentUser(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toBeNull();
        });

        it('error is thrown for non-401 server errors', async () => {
            mockGet.mockRejectedValue(new Error('Server Error'));

            const { result } = renderHook(() => useCurrentUser(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error).toBeInstanceOf(Error);
        });

        it('query is not retried on failure', async () => {
            mockGet.mockRejectedValue({ response: { status: 401 } });

            renderHook(() => useCurrentUser(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(mockGet).toHaveBeenCalledTimes(1));

            // Wait a bit to ensure no retries
            await new Promise(resolve => setTimeout(resolve, 100));
            expect(mockGet).toHaveBeenCalledTimes(1);
        });
    });
});
