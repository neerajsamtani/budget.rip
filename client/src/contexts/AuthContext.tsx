import React, { createContext, useContext, ReactNode, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useCurrentUser, User, authQueryKeys } from '../hooks/useAuth';
import { useLogin as useLoginMutation, useLogout as useLogoutMutation } from '../hooks/useApi';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const { data: user, isLoading, isFetched } = useCurrentUser();
  const loginMutation = useLoginMutation();
  const logoutMutation = useLogoutMutation();

  const login = useCallback(async (email: string, password: string) => {
    await loginMutation.mutateAsync({ email, password });
    // Refetch current user after successful login
    await queryClient.invalidateQueries({ queryKey: authQueryKeys.currentUser });
  }, [loginMutation, queryClient]);

  const logout = useCallback(async () => {
    await logoutMutation.mutateAsync();
    // Clear user data after logout
    queryClient.setQueryData(authQueryKeys.currentUser, null);
    // Invalidate all queries to clear cached data
    queryClient.clear();
  }, [logoutMutation, queryClient]);

  const value: AuthContextType = {
    user: user ?? null,
    isLoading: isLoading || !isFetched,
    isAuthenticated: !!user,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
