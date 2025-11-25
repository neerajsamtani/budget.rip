import { Spinner } from '@/components/ui/spinner';
import { act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import { AuthProvider, useAuth } from '../AuthContext';

// Mock sonner toast
jest.mock('sonner', () => {
    const mockToast = jest.fn();
    return {
        toast: Object.assign(mockToast, {
            success: jest.fn(),
            error: jest.fn(),
            warning: jest.fn(),
            info: jest.fn(),
        }),
    };
});

// Test component to consume auth context
const TestComponent = () => {
    const { user, isAuthenticated, isLoading, login, logout } = useAuth();

    const handleLogin = async () => {
        try {
            await login('test@example.com', 'password123');
        } catch {
            // Error handled by context
        }
    };

    const handleLogout = async () => {
        try {
            await logout();
        } catch {
            // Error handled by context
        }
    };

    if (isLoading) {
        return <div data-testid="loading"><Spinner size="lg" /></div>;
    }

    return (
        <div>
            <div data-testid="auth-status">
                {isAuthenticated ? 'authenticated' : 'not-authenticated'}
            </div>
            {user && (
                <div data-testid="user-email">{user.email}</div>
            )}
            <button onClick={handleLogin} data-testid="login-button">Login</button>
            <button onClick={handleLogout} data-testid="logout-button">Logout</button>
        </div>
    );
};

describe('AuthContext', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Initial State', () => {
        it('shows not-authenticated when /api/auth/me returns 401', async () => {
            mockAxiosInstance.get.mockRejectedValue({ response: { status: 401 } });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
            });
        });

        it('shows authenticated when /api/auth/me returns user', async () => {
            const mockUser = {
                id: 'user_123',
                email: 'test@example.com',
                first_name: 'Test',
                last_name: 'User',
            };
            mockAxiosInstance.get.mockResolvedValue({ data: mockUser });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
                expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
            });
        });
    });

    describe('Login', () => {
        it('calls login API with correct credentials', async () => {
            // Initially not authenticated
            mockAxiosInstance.get.mockRejectedValue({ response: { status: 401 } });
            // Login succeeds
            mockAxiosInstance.post.mockResolvedValue({ data: { login: true } });

            await act(async () => {
                render(
                    <AuthProvider>
                        <TestComponent />
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
            });

            const loginButton = screen.getByTestId('login-button');
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    'api/auth/login',
                    { email: 'test@example.com', password: 'password123' }
                );
            });
        });
    });

    describe('Logout', () => {
        it('calls logout API', async () => {
            // Initially authenticated
            mockAxiosInstance.get.mockResolvedValue({
                data: {
                    id: 'user_123',
                    email: 'test@example.com',
                    first_name: 'Test',
                    last_name: 'User',
                },
            });
            // Logout succeeds
            mockAxiosInstance.post.mockResolvedValue({ data: { logout: true } });

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
                expect(mockAxiosInstance.post).toHaveBeenCalledWith('api/auth/logout');
            });
        });
    });

    describe('useAuth hook', () => {
        it('throws error when used outside AuthProvider', () => {
            // Suppress console.error for this test
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => { });

            expect(() => {
                render(<TestComponent />);
            }).toThrow('useAuth must be used within an AuthProvider');

            consoleSpy.mockRestore();
        });
    });
});
