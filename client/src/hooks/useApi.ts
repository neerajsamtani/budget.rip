import { useMutation, useQuery, useQueryClient, UseMutationResult, UseQueryResult } from '@tanstack/react-query';
import axiosInstance from '../utils/axiosInstance';
import { EventInterface } from '../components/Event';
import { LineItemInterface } from '../contexts/LineItemsContext';

// Query Keys
export const queryKeys = {
  events: (startTime?: number, endTime?: number) => ['events', startTime, endTime] as const,
  lineItems: (params?: { reviewed?: boolean; paymentMethod?: string; eventId?: string }) =>
    ['lineItems', params] as const,
  eventLineItems: (eventId: string) => ['eventLineItems', eventId] as const,
  monthlyBreakdown: () => ['monthlyBreakdown'] as const,
  connectedAccounts: () => ['connectedAccounts'] as const,
  accountsAndBalances: () => ['accountsAndBalances'] as const,
  paymentMethods: () => ['paymentMethods'] as const,
};

// Query Hooks
export function useEvents(startTime?: number, endTime?: number): UseQueryResult<EventInterface[]> {
  return useQuery({
    queryKey: queryKeys.events(startTime, endTime),
    queryFn: async () => {
      const response = await axiosInstance.get('api/events', {
        params: {
          start_time: startTime,
          end_time: endTime,
        },
      });
      return response.data.data as EventInterface[];
    },
    enabled: !!startTime && !!endTime,
  });
}

export function useLineItems(params?: { reviewed?: boolean; paymentMethod?: string; eventId?: string; onlyLineItemsToReview?: boolean; enabled?: boolean }): UseQueryResult<LineItemInterface[]> {
  return useQuery({
    queryKey: queryKeys.lineItems(params),
    queryFn: async () => {
      const queryParams: Record<string, string | boolean> = {};

      if (params?.reviewed !== undefined) {
        queryParams.reviewed = params.reviewed;
      }
      if (params?.onlyLineItemsToReview) {
        queryParams.only_line_items_to_review = true;
      }
      if (params?.paymentMethod && params.paymentMethod !== 'All') {
        queryParams.payment_method = params.paymentMethod;
      }
      if (params?.eventId) {
        queryParams.event_id = params.eventId;
      }

      const response = await axiosInstance.get('api/line_items', { params: queryParams });
      return response.data.data as LineItemInterface[];
    },
    enabled: params?.enabled ?? true,
  });
}

export function useEventLineItems(eventId: string): UseQueryResult<LineItemInterface[]> {
  return useQuery({
    queryKey: queryKeys.eventLineItems(eventId),
    queryFn: async () => {
      const response = await axiosInstance.get(`api/events/${eventId}/line_items_for_event`);
      return response.data.data as LineItemInterface[];
    },
    enabled: !!eventId,
  });
}

interface MonthlyBreakdownData {
  [category: string]: Array<{ amount: number; date: string }>;
}

export function useMonthlyBreakdown(): UseQueryResult<MonthlyBreakdownData> {
  return useQuery({
    queryKey: queryKeys.monthlyBreakdown(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/monthly_breakdown');
      return response.data;
    },
  });
}

export function useConnectedAccounts(): UseQueryResult<unknown> {
  return useQuery({
    queryKey: queryKeys.connectedAccounts(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/connected_accounts');
      return response.data;
    },
  });
}

export function useAccountsAndBalances(): UseQueryResult<unknown> {
  return useQuery({
    queryKey: queryKeys.accountsAndBalances(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/accounts_and_balances');
      return response.data;
    },
  });
}

export function usePaymentMethods(): UseQueryResult<string[]> {
  return useQuery({
    queryKey: queryKeys.paymentMethods(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/payment_methods');
      return Array.isArray(response.data) ? response.data : [];
    },
  });
}

// Mutation Hooks
interface CreateEventData {
  name: string;
  category: string;
  line_items: string[];
  date?: string;
  is_duplicate_transaction?: boolean;
  tags?: string[];
}

export function useCreateEvent(): UseMutationResult<unknown, Error, CreateEventData> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (eventData: CreateEventData) => {
      const response = await axiosInstance.post('api/events', eventData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['lineItems'] });
      queryClient.invalidateQueries({ queryKey: ['monthlyBreakdown'] });
    },
  });
}

interface CreateCashTransactionData {
  name: string;
  category: string;
  amount: number;
  date: number;
  tags?: string[];
}

export function useCreateCashTransaction(): UseMutationResult<unknown, Error, CreateCashTransactionData> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (transactionData: CreateCashTransactionData) => {
      const response = await axiosInstance.post('api/cash_transaction', transactionData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['lineItems'] });
      queryClient.invalidateQueries({ queryKey: ['monthlyBreakdown'] });
    },
  });
}

export function useDeleteEvent(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (eventId: string) => {
      await axiosInstance.delete(`api/events/${eventId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['lineItems'] });
      queryClient.invalidateQueries({ queryKey: ['monthlyBreakdown'] });
    },
  });
}

interface LoginCredentials {
  email: string;
  password: string;
}

export function useLogin(): UseMutationResult<unknown, Error, LoginCredentials> {
  return useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const response = await axiosInstance.post('api/auth/login', credentials);
      return response.data;
    },
  });
}

export function useLogout(): UseMutationResult<void, Error, void> {
  return useMutation({
    mutationFn: async () => {
      await axiosInstance.post('api/auth/logout');
    },
  });
}

export function useRefreshAllData(): UseMutationResult<LineItemInterface[], Error, void> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await axiosInstance.post('api/refresh/all');
      return response.data.data as LineItemInterface[];
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['lineItems'] });
      queryClient.invalidateQueries({ queryKey: ['monthlyBreakdown'] });
    },
  });
}

interface RefreshAccountData {
  accountId: string;
  source: 'stripe' | 'venmo' | 'splitwise';
}

export function useRefreshAccount(): UseMutationResult<void, Error, RefreshAccountData> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ accountId, source }: RefreshAccountData) => {
      await axiosInstance.post('api/refresh/account', { accountId, source });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectedAccounts'] });
      queryClient.invalidateQueries({ queryKey: ['accountsAndBalances'] });
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['lineItems'] });
      queryClient.invalidateQueries({ queryKey: ['monthlyBreakdown'] });
    },
  });
}

export function useSubscribeToAccount(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (accountId: string) => {
      await axiosInstance.post('api/subscribe_to_account', { account_id: accountId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectedAccounts'] });
      queryClient.invalidateQueries({ queryKey: ['accountsAndBalances'] });
    },
  });
}

export function useRelinkAccount(): UseMutationResult<string, Error, string> {
  return useMutation({
    mutationFn: async (accountId: string) => {
      const response = await axiosInstance.post(`api/relink_account/${accountId}`);
      return response.data.clientSecret;
    },
  });
}

export function useCreateFinancialConnectionsSession(): UseMutationResult<string, Error, void> {
  return useMutation({
    mutationFn: async () => {
      const response = await axiosInstance.post('api/create-fc-session');
      return response.data.clientSecret;
    },
  });
}
