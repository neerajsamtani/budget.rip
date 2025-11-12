import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '../utils/axiosInstance';
import { EventInterface } from '../components/Event';
import { LineItemInterface } from '../contexts/LineItemsContext';

// Query Keys
export const queryKeys = {
  events: (startTime?: number, endTime?: number) => ['events', startTime, endTime] as const,
  lineItems: (params?: { reviewed?: boolean; paymentMethod?: string; eventId?: string }) =>
    ['lineItems', params] as const,
  monthlyBreakdown: () => ['monthlyBreakdown'] as const,
  accounts: () => ['accounts'] as const,
  financialConnectionsAccounts: () => ['financialConnectionsAccounts'] as const,
  connectedAccounts: () => ['connectedAccounts'] as const,
  accountsAndBalances: () => ['accountsAndBalances'] as const,
};

// Query Hooks
export function useEvents(startTime?: number, endTime?: number) {
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

export function useLineItems(params?: { reviewed?: boolean; paymentMethod?: string; eventId?: string; onlyLineItemsToReview?: boolean }) {
  return useQuery({
    queryKey: queryKeys.lineItems(params),
    queryFn: async () => {
      const queryParams: Record<string, any> = {};

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
  });
}

export function useEventLineItems(eventId: string) {
  return useQuery({
    queryKey: ['eventLineItems', eventId],
    queryFn: async () => {
      const response = await axiosInstance.get(`api/events/${eventId}/line_items_for_event`);
      return response.data.data as LineItemInterface[];
    },
    enabled: !!eventId,
  });
}

export function useMonthlyBreakdown() {
  return useQuery({
    queryKey: queryKeys.monthlyBreakdown(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/monthly_breakdown');
      return response.data.data;
    },
  });
}

export function useAccounts() {
  return useQuery({
    queryKey: queryKeys.accounts(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/accounts');
      return response.data.data;
    },
  });
}

export function useFinancialConnectionsAccounts() {
  return useQuery({
    queryKey: queryKeys.financialConnectionsAccounts(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/financial_connections/accounts');
      return response.data.data;
    },
  });
}

export function useConnectedAccounts() {
  return useQuery({
    queryKey: queryKeys.connectedAccounts(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/connected_accounts');
      return response.data;
    },
  });
}

export function useAccountsAndBalances() {
  return useQuery({
    queryKey: queryKeys.accountsAndBalances(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/accounts_and_balances');
      return response.data;
    },
  });
}

// Mutation Hooks
export function useCreateEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (eventData: {
      name: string;
      category: string;
      line_items: string[];
      tags?: string[];
    }) => {
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

export function useCreateCashTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (transactionData: {
      name: string;
      category: string;
      amount: number;
      date: number;
      tags?: string[];
    }) => {
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

export function useDeleteEvent() {
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

export function useLogin() {
  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const response = await axiosInstance.post('api/auth/login', credentials);
      return response.data;
    },
  });
}

export function useLogout() {
  return useMutation({
    mutationFn: async () => {
      await axiosInstance.post('api/auth/logout');
    },
  });
}

export function useRefreshAllData() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await axiosInstance.get('api/refresh/all');
      return response.data.data as LineItemInterface[];
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['lineItems'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['financialConnectionsAccounts'] });
      queryClient.invalidateQueries({ queryKey: ['monthlyBreakdown'] });
    },
  });
}

export function useSubscribeToAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (accountId: string) => {
      await axiosInstance.get('api/subscribe_to_account', {
        params: { account_id: accountId },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['financialConnectionsAccounts'] });
    },
  });
}

export function useRelinkAccount() {
  return useMutation({
    mutationFn: async (accountId: string) => {
      const response = await axiosInstance.get(`api/relink_account/${accountId}`);
      return response.data.clientSecret;
    },
  });
}

export function useCreateFinancialConnectionsSession() {
  return useMutation({
    mutationFn: async () => {
      const response = await axiosInstance.post('api/create-fc-session');
      return response.data.clientSecret;
    },
  });
}

export function useSubscribeToAccountMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (accountId: string) => {
      await axiosInstance.get(`api/subscribe_to_account/${accountId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectedAccounts'] });
      queryClient.invalidateQueries({ queryKey: ['accountsAndBalances'] });
    },
  });
}
