import { act } from '@testing-library/react';
import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import { AuthProvider } from '../../contexts/AuthContext';
import { ProtectedRoute } from '../ProtectedRoute';

// Mock Navigate component from react-router-dom
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    Navigate: jest.fn(({ to }) => <div data-testid="navigate-mock">Redirected to {to}</div>),
}));

const ProtectedContent = () => (
    <div data-testid="protected-content">Protected Content</div>
);

const LoginPage = () => (
    <div data-testid="login-page">Login Page</div>
);

const TestApp = () => (
    <Routes>
        <Route path="/" element={<ProtectedRoute><ProtectedContent /></ProtectedRoute>} />
        <Route path="/login" element={<LoginPage />} />
    </Routes>
);

describe('ProtectedRoute', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        (Navigate as jest.Mock).mockClear();
    });

    describe('Loading State', () => {
        it('shows loading indicator while checking authentication', () => {
            // Mock a delayed response to keep loading state
            mockAxiosInstance.get.mockImplementation(
                () => new Promise(resolve => setTimeout(() => resolve({ data: {} }), 100))
            );

            render(
                <AuthProvider>
                    <ProtectedRoute>
                        <ProtectedContent />
                    </ProtectedRoute>
                </AuthProvider>
            );

            expect(screen.getByText('Loading...')).toBeInTheDocument();
        });

        it('removes loading indicator after authentication check completes', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
            });
        });
    });

    describe('Authenticated User', () => {
        it('renders children when user is authenticated', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('protected-content')).toBeInTheDocument();
            });
        });

        it('does not redirect when user is authenticated', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('protected-content')).toBeInTheDocument();
            });

            expect(Navigate).not.toHaveBeenCalled();
        });

        it('renders complex children correctly', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            const ComplexChild = () => (
                <div>
                    <h1 data-testid="title">Dashboard</h1>
                    <p data-testid="subtitle">Welcome back!</p>
                    <button data-testid="action-button">Take Action</button>
                </div>
            );

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ComplexChild />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('title')).toBeInTheDocument();
                expect(screen.getByTestId('subtitle')).toBeInTheDocument();
                expect(screen.getByTestId('action-button')).toBeInTheDocument();
            });
        });
    });

    describe('Unauthenticated User', () => {
        it('redirects to /login when user is not authenticated', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(Navigate).toHaveBeenCalledWith(
                    expect.objectContaining({ to: '/login', replace: true }),
                    expect.anything()
                );
            });
        });

        it('does not render children when user is not authenticated', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(Navigate).toHaveBeenCalled();
            });

            expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
        });

        it('uses replace prop in Navigate to avoid history issues', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(Navigate).toHaveBeenCalledWith(
                    expect.objectContaining({ replace: true }),
                    expect.anything()
                );
            });
        });
    });

    describe('Authentication State Changes', () => {
        it('redirects to login when auth check fails', async () => {
            // Start unauthenticated
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(Navigate).toHaveBeenCalledWith(
                    expect.objectContaining({ to: '/login' }),
                    expect.anything()
                );
            });
        });
    });

    describe('Error Handling', () => {
        it('handles 401 unauthorized error', async () => {
            const error = new Error('Unauthorized');
            // @ts-ignore
            error.response = { status: 401 };
            mockAxiosInstance.get.mockRejectedValue(error);

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(Navigate).toHaveBeenCalledWith(
                    expect.objectContaining({ to: '/login' }),
                    expect.anything()
                );
            });
        });

        it('handles network errors', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Network error'));

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(Navigate).toHaveBeenCalledWith(
                    expect.objectContaining({ to: '/login' }),
                    expect.anything()
                );
            });
        });

        it('handles timeout errors', async () => {
            const timeoutError = new Error('timeout of 5000ms exceeded');
            // @ts-ignore
            timeoutError.code = 'ECONNABORTED';
            mockAxiosInstance.get.mockRejectedValue(timeoutError);

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(Navigate).toHaveBeenCalledWith(
                    expect.objectContaining({ to: '/login' }),
                    expect.anything()
                );
            });
        });
    });

    describe('Multiple ProtectedRoutes', () => {
        it('applies protection to all wrapped routes', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Unauthorized'));

            const Page1 = () => <div data-testid="page1">Page 1</div>;
            const Page2 = () => <div data-testid="page2">Page 2</div>;

            await act(async () => {
                render(
                    <AuthProvider>
                        <div>
                            <ProtectedRoute>
                                <Page1 />
                            </ProtectedRoute>
                            <ProtectedRoute>
                                <Page2 />
                            </ProtectedRoute>
                        </div>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(Navigate).toHaveBeenCalledTimes(2);
            });

            expect(screen.queryByTestId('page1')).not.toBeInTheDocument();
            expect(screen.queryByTestId('page2')).not.toBeInTheDocument();
        });

        it('renders all protected routes when authenticated', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            const Page1 = () => <div data-testid="page1">Page 1</div>;
            const Page2 = () => <div data-testid="page2">Page 2</div>;

            await act(async () => {
                render(
                    <AuthProvider>
                        <div>
                            <ProtectedRoute>
                                <Page1 />
                            </ProtectedRoute>
                            <ProtectedRoute>
                                <Page2 />
                            </ProtectedRoute>
                        </div>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('page1')).toBeInTheDocument();
                expect(screen.getByTestId('page2')).toBeInTheDocument();
            });

            expect(Navigate).not.toHaveBeenCalled();
        });
    });

    describe('Integration with AuthProvider', () => {
        it('uses authentication state from AuthProvider', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/connected_accounts');
                expect(screen.getByTestId('protected-content')).toBeInTheDocument();
            });
        });

        it('responds to authentication changes from AuthProvider', async () => {
            let resolveAuth: (value: any) => void;
            const authPromise = new Promise(resolve => {
                resolveAuth = resolve;
            });

            mockAxiosInstance.get.mockReturnValue(authPromise);

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ProtectedContent />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            // Should show loading
            expect(screen.getByText('Loading...')).toBeInTheDocument();

            // Resolve authentication
            await act(async () => {
                resolveAuth!({ data: {} });
            });

            await waitFor(() => {
                expect(screen.getByTestId('protected-content')).toBeInTheDocument();
            });
        });
    });

    describe('Props and Children', () => {
        it('accepts and renders React elements as children', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <div data-testid="custom-element">Custom Element</div>
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('custom-element')).toBeInTheDocument();
            });
        });

        it('handles children with props', async () => {
            mockAxiosInstance.get.mockResolvedValue({ data: {} });

            const ChildWithProps = ({ message }: { message: string }) => (
                <div data-testid="child-with-props">{message}</div>
            );

            await act(async () => {
                render(
                    <AuthProvider>
                        <ProtectedRoute>
                            <ChildWithProps message="Hello World" />
                        </ProtectedRoute>
                    </AuthProvider>
                );
            });

            await waitFor(() => {
                expect(screen.getByTestId('child-with-props')).toHaveTextContent('Hello World');
            });
        });
    });
});
