import { act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';

// Mock axios - must be before imports that use it
jest.mock('../../utils/axiosInstance', () => ({
    __esModule: true,
    default: {
        get: jest.fn(),
        post: jest.fn(),
    },
}));

import axiosInstance from '../../utils/axiosInstance';
const mockGet = axiosInstance.get as jest.Mock;
const mockPost = axiosInstance.post as jest.Mock;

import LoginPage from '../LoginPage';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: null }),
}));

const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false },
    },
});

const renderLoginPage = () => {
    const queryClient = createTestQueryClient();
    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter>
                <AuthProvider>
                    <LoginPage />
                </AuthProvider>
            </MemoryRouter>
        </QueryClientProvider>
    );
};

describe('LoginPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Default: user is not authenticated
        mockGet.mockRejectedValue({ response: { status: 401 } });
        mockPost.mockResolvedValue({ data: { login: true } });
    });

    describe('Rendering', () => {
        it('login form displays all required elements', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });
            expect(screen.getByLabelText('Password')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
        });

        it('logout button is not present on login page', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });
            expect(screen.queryByRole('button', { name: /log out/i })).not.toBeInTheDocument();
        });

        it('form fields have correct input types', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email') as HTMLInputElement;
            const passwordField = screen.getByLabelText('Password') as HTMLInputElement;

            expect(emailField.type).toBe('text');
            expect(passwordField.type).toBe('password');
        });

        it('form fields start with empty values', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email') as HTMLInputElement;
            const passwordField = screen.getByLabelText('Password') as HTMLInputElement;

            expect(emailField.value).toBe('');
            expect(passwordField.value).toBe('');
        });
    });

    describe('User Interactions', () => {
        it('email field accepts user input', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email');
            fireEvent.change(emailField, { target: { value: 'test@example.com' } });

            expect(emailField).toHaveValue('test@example.com');
        });

        it('password field accepts user input', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Password')).toBeInTheDocument();
            });

            const passwordField = screen.getByLabelText('Password');
            fireEvent.change(passwordField, { target: { value: 'password123' } });

            expect(passwordField).toHaveValue('password123');
        });

        it('login API is called when Log In button is clicked', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email');
            const passwordField = screen.getByLabelText('Password');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(mockPost).toHaveBeenCalledWith(
                    'api/auth/login',
                    {
                        email: 'test@example.com',
                        password: 'password123'
                    }
                );
            });
        });

        it('user is redirected to home page after successful login', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email');
            const passwordField = screen.getByLabelText('Password');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
            });
        });

        it('form fields are cleared after successful login', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email');
            const passwordField = screen.getByLabelText('Password');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(emailField).toHaveValue('');
                expect(passwordField).toHaveValue('');
            });
        });
    });

    describe('Error Handling', () => {
        it('error message is shown when login API fails', async () => {
            mockPost.mockRejectedValue(new Error('Login failed'));

            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email');
            const passwordField = screen.getByLabelText('Password');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(screen.getByRole('alert')).toHaveTextContent('Login failed');
            });
        });

        it('user stays on login page when login fails', async () => {
            mockPost.mockRejectedValue(new Error('Login failed'));

            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email');
            const passwordField = screen.getByLabelText('Password');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(screen.getByRole('alert')).toBeInTheDocument();
            });
            expect(mockNavigate).not.toHaveBeenCalled();
        });
    });

    describe('Accessibility', () => {
        it('form fields have proper labels', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });
            expect(screen.getByLabelText('Password')).toBeInTheDocument();
        });

        it('buttons have proper labels', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
            });
        });
    });

    describe('Form Validation', () => {
        it('required field validation prevents empty submission', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
            });

            const submitButton = screen.getByRole('button', { name: /log in/i });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            // Form should not submit without required fields
            expect(mockPost).not.toHaveBeenCalled();
            expect(screen.getByRole('alert')).toHaveTextContent(/required/i);
        });

        it('invalid email format prevents form submission', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
            });

            const emailInput = screen.getByLabelText(/email/i);
            const passwordInput = screen.getByLabelText(/password/i);
            const submitButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
            fireEvent.change(passwordInput, { target: { value: 'password123' } });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            // Form should not submit with invalid email
            expect(mockPost).not.toHaveBeenCalled();
            expect(screen.getByRole('alert')).toHaveTextContent(/valid email/i);
        });

        it('special characters in email and password are handled correctly', async () => {
            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email');
            const passwordField = screen.getByLabelText('Password');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test+tag@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'pass@word!123' } });
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(mockPost).toHaveBeenCalledWith(
                    'api/auth/login',
                    {
                        email: 'test+tag@example.com',
                        password: 'pass@word!123'
                    }
                );
            });
        });
    });

    describe('Loading State', () => {
        it('button shows loading state and is disabled during login', async () => {
            // Make login hang
            mockPost.mockImplementation(() => new Promise(() => {}));

            await act(async () => {
                renderLoginPage();
            });

            await waitFor(() => {
                expect(screen.getByLabelText('Email')).toBeInTheDocument();
            });

            const emailField = screen.getByLabelText('Email');
            const passwordField = screen.getByLabelText('Password');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });

            await act(async () => {
                userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /logging in/i })).toBeDisabled();
            });
        });
    });
});
