import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import React from 'react';

// Mock axios instance - define mocks inline in the factory to avoid hoisting issues
jest.mock('../../utils/axiosInstance', () => ({
    __esModule: true,
    default: {
        get: jest.fn(),
        post: jest.fn(),
        delete: jest.fn(),
    },
}));

// Import the mocked module to get references to the mock functions
import axiosInstance from '../../utils/axiosInstance';
const mockGet = axiosInstance.get as jest.Mock;
const mockPost = axiosInstance.post as jest.Mock;
const mockDelete = axiosInstance.delete as jest.Mock;

import {
    queryKeys,
    useCreateEvent,
    useCreateManualTransaction,
    useDeleteEvent,
    useEventLineItems,
    useEvents,
    useLineItems,
    useLogin,
    useLogout,
    useMonthlyBreakdown,
    usePaymentMethods,
} from '../useApi';

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

describe('useApi hooks', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('queryKeys', () => {
        it('events query key includes date range parameters', () => {
            expect(queryKeys.events(1000, 2000)).toEqual(['events', 1000, 2000]);
            expect(queryKeys.events()).toEqual(['events', undefined, undefined]);
        });

        it('lineItems query key includes filter parameters', () => {
            expect(queryKeys.lineItems({ onlyLineItemsToReview: true })).toEqual(['lineItems', { onlyLineItemsToReview: true }]);
            expect(queryKeys.lineItems({ paymentMethod: 'cash' })).toEqual(['lineItems', { paymentMethod: 'cash' }]);
            expect(queryKeys.lineItems()).toEqual(['lineItems', undefined]);
        });

        it('eventLineItems query key includes event ID', () => {
            expect(queryKeys.eventLineItems('event-123')).toEqual(['eventLineItems', 'event-123']);
        });

        it('static endpoint query keys have correct format', () => {
            expect(queryKeys.monthlyBreakdown()).toEqual(['monthlyBreakdown']);
            expect(queryKeys.connectedAccounts()).toEqual(['connectedAccounts']);
            expect(queryKeys.paymentMethods()).toEqual(['paymentMethods']);
        });
    });

    describe('useEvents', () => {
        it('events are fetched with date range parameters', async () => {
            const mockEvents = [
                { id: '1', name: 'Event 1', amount: 100, date: 1640995200 },
                { id: '2', name: 'Event 2', amount: 200, date: 1641081600 },
            ];
            mockGet.mockResolvedValue({ data: { data: mockEvents } });

            const { result } = renderHook(() => useEvents(1640000000, 1650000000), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/events', {
                params: { start_time: 1640000000, end_time: 1650000000 },
            });
            expect(result.current.data).toEqual(mockEvents);
        });

        it('events query is disabled when date range is incomplete', () => {
            renderHook(() => useEvents(undefined, 1650000000), { wrapper: createWrapper() });

            expect(mockGet).not.toHaveBeenCalled();
        });

        it('API error sets error state', async () => {
            mockGet.mockRejectedValue(new Error('API Error'));

            const { result } = renderHook(() => useEvents(1640000000, 1650000000), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error).toBeInstanceOf(Error);
        });
    });

    describe('useLineItems', () => {
        it('line items are fetched without parameters', async () => {
            const mockLineItems = [{ id: '1', description: 'Item 1', amount: 50 }];
            mockGet.mockResolvedValue({ data: { data: mockLineItems } });

            const { result } = renderHook(() => useLineItems(), { wrapper: createWrapper() });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/line_items', { params: {} });
            expect(result.current.data).toEqual(mockLineItems);
        });

        it('fetches line items with onlyLineItemsToReview filter', async () => {
            mockGet.mockResolvedValue({ data: { data: [] } });

            const { result } = renderHook(() => useLineItems({ onlyLineItemsToReview: true }), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/line_items', {
                params: { only_line_items_to_review: true },
            });
        });

        it('fetches line items with payment method filter', async () => {
            mockGet.mockResolvedValue({ data: { data: [] } });

            const { result } = renderHook(() => useLineItems({ paymentMethod: 'Chase Debit Card' }), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/line_items', {
                params: { payment_method: 'Chase Debit Card' },
            });
        });

        it('does not include payment method when set to "All"', async () => {
            mockGet.mockResolvedValue({ data: { data: [] } });

            const { result } = renderHook(() => useLineItems({ paymentMethod: 'All' }), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/line_items', { params: {} });
        });

        it('fetches line items to review', async () => {
            mockGet.mockResolvedValue({ data: { data: [] } });

            const { result } = renderHook(() => useLineItems({ onlyLineItemsToReview: true }), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/line_items', {
                params: { only_line_items_to_review: true },
            });
        });
    });

    describe('useEventLineItems', () => {
        it('fetches line items for a specific event', async () => {
            const mockLineItems = [{ id: '1', description: 'Event Line Item', amount: 25 }];
            mockGet.mockResolvedValue({ data: { data: mockLineItems } });

            const { result } = renderHook(() => useEventLineItems('event-123'), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/events/event-123/line_items_for_event');
            expect(result.current.data).toEqual(mockLineItems);
        });

        it('does not fetch when eventId is empty', () => {
            renderHook(() => useEventLineItems(''), { wrapper: createWrapper() });

            expect(mockGet).not.toHaveBeenCalled();
        });
    });

    describe('useMonthlyBreakdown', () => {
        it('fetches monthly breakdown data', async () => {
            const mockData = {
                Dining: [{ amount: 100, date: '2024-01' }],
                Groceries: [{ amount: 200, date: '2024-01' }],
            };
            mockGet.mockResolvedValue({ data: mockData });

            const { result } = renderHook(() => useMonthlyBreakdown(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/monthly_breakdown');
            expect(result.current.data).toEqual(mockData);
        });
    });

    describe('usePaymentMethods', () => {
        it('fetches payment methods', async () => {
            const mockMethods = [
                { id: 'pm_1', name: 'Bank of America Credit Card', type: 'credit', is_active: true },
                { id: 'pm_2', name: 'cash', type: 'cash', is_active: true },
                { id: 'pm_3', name: 'Chase Debit Card', type: 'debit', is_active: true },
            ];
            mockGet.mockResolvedValue({ data: { data: mockMethods } });

            const { result } = renderHook(() => usePaymentMethods(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(mockGet).toHaveBeenCalledWith('api/payment_methods');
            expect(result.current.data).toEqual(mockMethods);
        });

        it('returns empty array when response data is empty', async () => {
            mockGet.mockResolvedValue({ data: { data: [] } });

            const { result } = renderHook(() => usePaymentMethods(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual([]);
        });
    });

    describe('useCreateEvent', () => {
        it('creates an event and invalidates queries', async () => {
            mockPost.mockResolvedValue({ data: { id: 'new-event' } });

            const queryClient = createTestQueryClient();
            const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useCreateEvent(), { wrapper });

            await act(async () => {
                await result.current.mutateAsync({
                    name: 'New Event',
                    category: 'Dining',
                    line_items: ['line-1', 'line-2'],
                });
            });

            expect(mockPost).toHaveBeenCalledWith('api/events', {
                name: 'New Event',
                category: 'Dining',
                line_items: ['line-1', 'line-2'],
            });

            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['events'] });
            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['lineItems'] });
            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['monthlyBreakdown'] });
            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['tags'] });
        });

        it('handles mutation errors', async () => {
            mockPost.mockRejectedValue(new Error('Create failed'));

            const { result } = renderHook(() => useCreateEvent(), { wrapper: createWrapper() });

            await expect(
                result.current.mutateAsync({
                    name: 'New Event',
                    category: 'Dining',
                    line_items: [],
                })
            ).rejects.toThrow('Create failed');
        });
    });

    describe('useCreateManualTransaction', () => {
        it('creates a manual transaction', async () => {
            mockPost.mockResolvedValue({ data: { transaction_id: 'manual_123' } });

            const { result } = renderHook(() => useCreateManualTransaction(), {
                wrapper: createWrapper(),
            });

            await act(async () => {
                await result.current.mutateAsync({
                    date: '2024-01-15',
                    person: 'John Doe',
                    description: 'Cash Payment',
                    amount: 50,
                    payment_method_id: 'pm_cash',
                });
            });

            expect(mockPost).toHaveBeenCalledWith('api/manual_transaction', {
                date: '2024-01-15',
                person: 'John Doe',
                description: 'Cash Payment',
                amount: 50,
                payment_method_id: 'pm_cash',
            });
        });
    });

    describe('useDeleteEvent', () => {
        it('deletes an event and invalidates queries', async () => {
            mockDelete.mockResolvedValue({});

            const queryClient = createTestQueryClient();
            const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useDeleteEvent(), { wrapper });

            await act(async () => {
                await result.current.mutateAsync('event-to-delete');
            });

            expect(mockDelete).toHaveBeenCalledWith('api/events/event-to-delete');
            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['events'] });
            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['lineItems'] });
            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['tags'] });
        });
    });

    describe('useLogin', () => {
        it('logs in with credentials', async () => {
            mockPost.mockResolvedValue({ data: { token: 'jwt-token' } });

            const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });

            await act(async () => {
                await result.current.mutateAsync({
                    email: 'test@example.com',
                    password: 'password123',
                });
            });

            expect(mockPost).toHaveBeenCalledWith('api/auth/login', {
                email: 'test@example.com',
                password: 'password123',
            });
        });

        it('handles login failure', async () => {
            mockPost.mockRejectedValue(new Error('Invalid credentials'));

            const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });

            await expect(
                result.current.mutateAsync({
                    email: 'test@example.com',
                    password: 'wrong-password',
                })
            ).rejects.toThrow('Invalid credentials');
        });
    });

    describe('useLogout', () => {
        it('logs out the user', async () => {
            mockPost.mockResolvedValue({});

            const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() });

            await act(async () => {
                await result.current.mutateAsync();
            });

            expect(mockPost).toHaveBeenCalledWith('api/auth/logout');
        });
    });
});
