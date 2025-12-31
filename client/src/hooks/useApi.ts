import { useMutation, useQuery, useQueryClient, UseMutationResult, UseQueryResult } from '@tanstack/react-query';
import axiosInstance from '../utils/axiosInstance';
import { EventInterface } from '../components/Event';
import { LineItemInterface } from '../contexts/LineItemsContext';

// Query Keys
export const queryKeys = {
  events: (startTime?: number, endTime?: number) => ['events', startTime, endTime] as const,
  lineItems: (params?: { onlyLineItemsToReview?: boolean; paymentMethod?: string }) =>
    ['lineItems', params] as const,
  eventLineItems: (eventId: string) => ['eventLineItems', eventId] as const,
  monthlyBreakdown: () => ['monthlyBreakdown'] as const,
  connectedAccounts: () => ['connectedAccounts'] as const,
  accountsAndBalances: () => ['accountsAndBalances'] as const,
  paymentMethods: () => ['paymentMethods'] as const,
  tags: () => ['tags'] as const,
  eventHints: () => ['eventHints'] as const,
  eventHintSuggestion: (lineItemIds: string[]) => ['eventHintSuggestion', lineItemIds] as const,
  categories: () => ['categories'] as const,
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

export function useLineItems(params?: { onlyLineItemsToReview?: boolean; paymentMethod?: string; enabled?: boolean }): UseQueryResult<LineItemInterface[]> {
  return useQuery({
    queryKey: queryKeys.lineItems(params ? { onlyLineItemsToReview: params.onlyLineItemsToReview, paymentMethod: params.paymentMethod } : undefined),
    queryFn: async () => {
      const queryParams: Record<string, string | boolean> = {};

      if (params?.onlyLineItemsToReview) {
        queryParams.only_line_items_to_review = true;
      }
      if (params?.paymentMethod && params.paymentMethod !== 'All') {
        queryParams.payment_method = params.paymentMethod;
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

export interface StripeAccount {
  id: string;
  institution_name: string;
  display_name: string;
  last4: string;
  status: 'active' | 'inactive';
  subcategory: string;
}

export interface ConnectedAccount {
  venmo?: string[];
  splitwise?: string[];
  stripe?: StripeAccount[];
}

export function useConnectedAccounts(): UseQueryResult<ConnectedAccount[]> {
  return useQuery({
    queryKey: queryKeys.connectedAccounts(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/connected_accounts');
      return response.data as ConnectedAccount[];
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

export interface Tag {
  id: string;
  name: string;
}

export function useTags(): UseQueryResult<Tag[]> {
  return useQuery({
    queryKey: queryKeys.tags(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/tags');
      return response.data.data as Tag[];
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
      queryClient.invalidateQueries({ queryKey: ['tags'] });
    },
  });
}

interface UpdateEventData {
  eventId: string;
  name: string;
  category: string;
  line_items: string[];
  date?: string;
  is_duplicate_transaction?: boolean;
  tags?: string[];
}

export function useUpdateEvent(): UseMutationResult<unknown, Error, UpdateEventData> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ eventId, ...eventData }: UpdateEventData) => {
      const response = await axiosInstance.put(`api/events/${eventId}`, eventData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['lineItems'] });
      queryClient.invalidateQueries({ queryKey: ['eventLineItems'] });
      queryClient.invalidateQueries({ queryKey: ['monthlyBreakdown'] });
      queryClient.invalidateQueries({ queryKey: ['tags'] });
    },
  });
}

export interface CreateCashTransactionData {
  date: string;        // YYYY-MM-DD format
  person: string;
  description: string;
  amount: number;
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
      queryClient.invalidateQueries({ queryKey: ['tags'] });
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

// Event Hints
export interface EventHint {
  id: string;
  name: string;
  cel_expression: string;
  prefill_name: string;
  prefill_category: string | null;
  prefill_category_id: string | null;
  display_order: number;
  is_active: boolean;
}

export interface EventHintSuggestion {
  name: string;
  category: string | null;
  matched_hint_id: string;
  matched_hint_name: string;
}

export interface CategoryOption {
  id: string;
  name: string;
}

export function useEventHints(): UseQueryResult<EventHint[]> {
  return useQuery({
    queryKey: queryKeys.eventHints(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/event-hints');
      return response.data.data as EventHint[];
    },
  });
}

export function useCategories(): UseQueryResult<CategoryOption[]> {
  return useQuery({
    queryKey: queryKeys.categories(),
    queryFn: async () => {
      const response = await axiosInstance.get('api/categories');
      return response.data.data as CategoryOption[];
    },
  });
}

interface CreateCategoryData {
  name: string;
}

export function useCreateCategory(): UseMutationResult<CategoryOption, Error, CreateCategoryData> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateCategoryData) => {
      const response = await axiosInstance.post('api/categories', data);
      return response.data.data as CategoryOption;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories() });
    },
  });
}

interface UpdateCategoryData {
  id: string;
  name?: string;
}

export function useUpdateCategory(): UseMutationResult<CategoryOption, Error, UpdateCategoryData> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...data }: UpdateCategoryData) => {
      const response = await axiosInstance.put(`api/categories/${id}`, data);
      return response.data.data as CategoryOption;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories() });
    },
  });
}

export function useDeleteCategory(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await axiosInstance.delete(`api/categories/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories() });
    },
  });
}

export function useEvaluateEventHints(lineItemIds: string[], enabled: boolean = true): UseQueryResult<EventHintSuggestion | null> {
  return useQuery({
    queryKey: queryKeys.eventHintSuggestion(lineItemIds),
    queryFn: async () => {
      if (lineItemIds.length === 0) return null;
      const response = await axiosInstance.post('api/event-hints/evaluate', { line_item_ids: lineItemIds });
      return response.data.data.suggestion as EventHintSuggestion | null;
    },
    enabled: enabled && lineItemIds.length > 0,
  });
}

interface CreateEventHintData {
  name: string;
  cel_expression: string;
  prefill_name: string;
  prefill_category_id?: string | null;
  is_active?: boolean;
}

export function useCreateEventHint(): UseMutationResult<EventHint, Error, CreateEventHintData> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateEventHintData) => {
      const response = await axiosInstance.post('api/event-hints', data);
      return response.data.data as EventHint;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.eventHints() });
      // Also invalidate suggestion cache since hints changed
      queryClient.invalidateQueries({ queryKey: ['eventHintSuggestion'] });
    },
  });
}

interface UpdateEventHintData {
  id: string;
  name?: string;
  cel_expression?: string;
  prefill_name?: string;
  prefill_category_id?: string | null;
  is_active?: boolean;
}

export function useUpdateEventHint(): UseMutationResult<EventHint, Error, UpdateEventHintData> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...data }: UpdateEventHintData) => {
      const response = await axiosInstance.put(`api/event-hints/${id}`, data);
      return response.data.data as EventHint;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.eventHints() });
      // Also invalidate suggestion cache since hints changed
      queryClient.invalidateQueries({ queryKey: ['eventHintSuggestion'] });
    },
  });
}

export function useDeleteEventHint(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await axiosInstance.delete(`api/event-hints/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.eventHints() });
      // Also invalidate suggestion cache since hints changed
      queryClient.invalidateQueries({ queryKey: ['eventHintSuggestion'] });
    },
  });
}

export function useReorderEventHints(): UseMutationResult<void, Error, string[]> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (hintIds: string[]) => {
      await axiosInstance.put('api/event-hints/reorder', { hint_ids: hintIds });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.eventHints() });
      // Also invalidate suggestion cache since order affects which hint matches first
      queryClient.invalidateQueries({ queryKey: ['eventHintSuggestion'] });
    },
  });
}

interface ValidateCelResult {
  is_valid: boolean;
  error?: string;
}

export function useValidateCelExpression(): UseMutationResult<ValidateCelResult, Error, string> {
  return useMutation({
    mutationFn: async (celExpression: string) => {
      const response = await axiosInstance.post('api/event-hints/validate', { cel_expression: celExpression });
      return response.data.data as ValidateCelResult;
    },
  });
}
