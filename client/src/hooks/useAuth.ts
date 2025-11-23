import { useQuery, UseQueryResult } from '@tanstack/react-query';
import axiosInstance from '../utils/axiosInstance';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export const authQueryKeys = {
  currentUser: ['currentUser'] as const,
};

export function useCurrentUser(): UseQueryResult<User | null> {
  return useQuery({
    queryKey: authQueryKeys.currentUser,
    queryFn: async () => {
      try {
        const response = await axiosInstance.get('api/auth/me');
        return response.data as User;
      } catch (error: any) {
        // If 401, user is not authenticated - this is not an error
        if (error.response?.status === 401) {
          return null;
        }
        throw error;
      }
    },
    retry: false, // Don't retry on 401
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
