import { act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import { AuthProvider, useAuth } from '../AuthContext';

// Test component to use the auth context
const TestComponent = () => {
    const { isAuthenticated, isLoading, login, logout, checkAuth } = useAuth();

    return (
        <div>
            <div data-testid="auth-status">
                {isLoading ? 'loading' : isAuthenticated ? 'authenticated' : 'unauthenticated'}
            </div>
            <button onClick={login} data-testid="login-button">Login</button>
            <button onClick={logout} data-testid="logout-button">Logout</button>
            <button onClick={checkAuth} data-testid="check-auth-button">Check Auth</button>
        </div>
    );
};

describe('AuthContext', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Provider Initialization', () => {
        it('renders children correctly', () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            render(
                <AuthProvider>
                    <div data-testid="child">Child Component</div>
                </AuthProvider>
            );

            expect(screen.getByTestId('child')).toBeInTheDocument();
        });

        it('starts with loading state', () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            render(
                <AuthProvider>
                    <TestComponent />
                </AuthProvider>
            );

            expect(screen.getByTestId('auth-status')).toHaveTextContent('loading');
        });

        it('checks authentication on mount with successful response', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/connected_accounts');
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });
        });

        it('sets unauthenticated state when API call fails', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });
        });

        it('completes loading after authentication check', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).not.toHaveTextContent('loading');
            });
        });
    });

    describe('Context Hooks', () => {
        it('throws error when useAuth is used outside AuthProvider', () => {
            // Suppress console.error for this test
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

            expect(() => {
                render(<TestComponent />);
            }).toThrow('useAuth must be used within an AuthProvider');

            consoleSpy.mockRestore();
        });

        it('provides auth state and functions through useAuth hook', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('login-button')).toBeInTheDocument();
                expect(screen.getByTestId('logout-button')).toBeInTheDocument();
                expect(screen.getByTestId('check-auth-button')).toBeInTheDocument();
            });
        });
    });

    describe('Login Function', () => {
        it('sets authenticated state when login is called', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });

            const loginButton = screen.getByTestId('login-button');
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });
        });

        it('updates state immediately without API call', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });

            // Clear previous mock calls
            mockAxiosInstance.get.mockClear();

            const loginButton = screen.getByTestId('login-button');
            await act(async () => {
                await userEvent.click(loginButton);
            });

            // Should not make API call during login (only during checkAuth)
            expect(mockAxiosInstance.get).not.toHaveBeenCalled();
            expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        });
    });

    describe('Logout Function', () => {
        it('calls logout API endpoint', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });
            mockAxiosInstance.post.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            const logoutButton = screen.getByTestId('logout-button');
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/auth/logout');
            });
        });

        it('sets unauthenticated state after logout', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });
            mockAxiosInstance.post.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            const logoutButton = screen.getByTestId('logout-button');
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });
        });

        it('sets unauthenticated state even if logout API fails', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });
            mockAxiosInstance.post.mockRejectedValue(new Error('Network error'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            const logoutButton = screen.getByTestId('logout-button');
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });
        });

        it('handles logout error gracefully', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });
            mockAxiosInstance.post.mockRejectedValue(new Error('Logout failed'));
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            const logoutButton = screen.getByTestId('logout-button');
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });

            consoleSpy.mockRestore();
        });
    });

    describe('CheckAuth Function', () => {
        it('calls connected_accounts API endpoint', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/connected_accounts');
            });
        });

        it('can be called manually to refresh auth state', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            mockAxiosInstance.get.mockClear();
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            const checkAuthButton = screen.getByTestId('check-auth-button');
            await act(async () => {
                await userEvent.click(checkAuthButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/connected_accounts');
            });
        });

        it('updates to unauthenticated if check fails', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            mockAxiosInstance.get.mockRejectedValue(new Error('Session expired'));

            const checkAuthButton = screen.getByTestId('check-auth-button');
            await act(async () => {
                await userEvent.click(checkAuthButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });
        });
    });

    describe('State Management', () => {
        it('maintains state across multiple operations', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });
            mockAxiosInstance.post.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            // Initially authenticated
            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            // Logout
            const logoutButton = screen.getByTestId('logout-button');
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });

            // Login
            const loginButton = screen.getByTestId('login-button');
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });
        });

        it('handles multiple logout calls', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });
            mockAxiosInstance.post.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            const logoutButton = screen.getByTestId('logout-button');

            // First logout
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });

            // Second logout (should not cause errors)
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });

            expect(mockAxiosInstance.post).toHaveBeenCalledTimes(2);
        });

        it('handles multiple login calls', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });

            const loginButton = screen.getByTestId('login-button');

            // First login
            await act(async () => {
                await userEvent.click(loginButton);
            });

            expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');

            // Second login (should not cause errors)
            await act(async () => {
                await userEvent.click(loginButton);
            });

            expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        });
    });

    describe('API Integration', () => {
        it('uses correct authentication check endpoint', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/connected_accounts');
            });
        });

        it('uses correct logout endpoint', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });
            mockAxiosInstance.post.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
            });

            const logoutButton = screen.getByTestId('logout-button');
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/auth/logout');
            });
        });

        it('handles network errors during authentication check', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Network error'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });
        });

        it('handles 401 unauthorized response', async () => {
            const error = new Error('Unauthorized');
            // @ts-ignore
            error.response = { status: 401 };
            mockAxiosInstance.get.mockRejectedValue(error);

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
            });
        });
    });
});
