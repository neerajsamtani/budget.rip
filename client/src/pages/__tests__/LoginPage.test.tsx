import { act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import LoginPage from '../LoginPage';

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

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
}));

describe('LoginPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockAxiosInstance.post.mockResolvedValue({ data: { success: true } });
    });

    describe('Rendering', () => {
        it('renders login form with all required elements', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            expect(screen.getByLabelText('Email')).toBeInTheDocument();
            expect(screen.getByLabelText('Password')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
        });

        it('renders form fields with correct types', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const emailField = screen.getByLabelText('Email') as HTMLInputElement;
            const passwordField = screen.getByLabelText('Password') as HTMLInputElement;

            expect(emailField.type).toBe('text');
            expect(passwordField.type).toBe('password');
        });

        it('renders form fields with empty initial values', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const emailField = screen.getByLabelText('Email') as HTMLInputElement;
            const passwordField = screen.getByLabelText('Password') as HTMLInputElement;

            expect(emailField.value).toBe('');
            expect(passwordField.value).toBe('');
        });
    });

    describe('User Interactions', () => {
        it('allows typing in email field', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const emailField = screen.getByLabelText('Email');
            fireEvent.change(emailField, { target: { value: 'test@example.com' } });

            expect(emailField).toHaveValue('test@example.com');
        });

        it('allows typing in password field', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const passwordField = screen.getByLabelText('Password');
            fireEvent.change(passwordField, { target: { value: 'password123' } });

            expect(passwordField).toHaveValue('password123');
        });

        it('calls login API when Log In button is clicked', async () => {
            await act(async () => {
                render(<LoginPage />);
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
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/auth/login'),
                    {
                        email: 'test@example.com',
                        password: 'password123'
                    }
                );
            });
        });

        it('calls logout API when Log Out button is clicked', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const logoutButton = screen.getByRole('button', { name: /log out/i });
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/auth/logout')
                );
            });
        });

        it('navigates to home page after successful login', async () => {
            await act(async () => {
                render(<LoginPage />);
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
                expect(mockNavigate).toHaveBeenCalledWith('/');
            });
        });

        it('clears form fields after successful login', async () => {
            await act(async () => {
                render(<LoginPage />);
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
        it('handles login API error gracefully', async () => {
            mockAxiosInstance.post.mockRejectedValue(new Error('Login failed'));

            await act(async () => {
                render(<LoginPage />);
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

        it('handles logout API error gracefully', async () => {
            mockAxiosInstance.post.mockRejectedValueOnce(new Error('Logout failed'));

            await act(async () => {
                render(<LoginPage />);
            });

            const logoutButton = screen.getByRole('button', { name: /log out/i });
            await act(async () => {
                await userEvent.click(logoutButton);
            });

            // Logout errors are not displayed in UI, just fail silently via TanStack Query
            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalled();
            });
        });

        it('does not navigate on login error', async () => {
            mockAxiosInstance.post.mockRejectedValue(new Error('Login failed'));

            await act(async () => {
                render(<LoginPage />);
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
                expect(mockNavigate).not.toHaveBeenCalled();
            });
        });
    });

    describe('Accessibility', () => {
        it('has proper form labels', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            expect(screen.getByLabelText('Email')).toBeInTheDocument();
            expect(screen.getByLabelText('Password')).toBeInTheDocument();
        });

        it('has proper button labels', () => {
            render(<LoginPage />);

            expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
        });

        it('has proper form structure', () => {
            render(<LoginPage />);

            // Check that form elements are present
            expect(screen.getByLabelText('Email')).toBeInTheDocument();
            expect(screen.getByLabelText('Password')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
        });
    });

    describe('Form Validation', () => {
        it('handles special characters in email and password', async () => {
            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email');
            const passwordField = screen.getByLabelText('Password');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test+tag@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'pass@word!123' } });
            await act(async () => {
                await userEvent.click(loginButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/auth/login'),
                    {
                        email: 'test+tag@example.com',
                        password: 'pass@word!123'
                    }
                );
            });
        });

        it('validates required fields', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const submitButton = screen.getByRole('button', { name: /log in/i });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            // Form should not submit without required fields
            expect(mockAxiosInstance.post).not.toHaveBeenCalled();
            expect(screen.getByRole('alert')).toHaveTextContent(/required/i);
        });

        it('validates email format', async () => {
            await act(async () => {
                render(<LoginPage />);
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
            expect(mockAxiosInstance.post).not.toHaveBeenCalled();
            expect(screen.getByRole('alert')).toHaveTextContent(/valid email/i);
        });

        it('does not submit when fields are empty and shows error', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const submitButton = screen.getByRole('button', { name: /log in/i });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            // Form should not submit without required fields
            expect(mockAxiosInstance.post).not.toHaveBeenCalled();
            expect(screen.getByRole('alert')).toHaveTextContent(/required/i);
        });
    });

    describe('Form Submission', () => {
        it('submits form with valid credentials', async () => {
            mockAxiosInstance.post.mockResolvedValueOnce({ data: { success: true } });

            await act(async () => {
                render(<LoginPage />);
            });

            const emailInput = screen.getByLabelText(/email/i);
            const passwordInput = screen.getByLabelText(/password/i);
            const submitButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordInput, { target: { value: 'password123' } });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/auth/login'),
                    {
                        email: 'test@example.com',
                        password: 'password123'
                    }
                );
            });
        });

        it('handles login failure', async () => {
            mockAxiosInstance.post.mockRejectedValueOnce(new Error('Login failed'));

            await act(async () => {
                render(<LoginPage />);
            });

            const emailInput = screen.getByLabelText(/email/i);
            const passwordInput = screen.getByLabelText(/password/i);
            const submitButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/auth/login'),
                    {
                        email: 'test@example.com',
                        password: 'wrongpassword'
                    }
                );
            });
        });

        it('validates required fields', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const submitButton = screen.getByRole('button', { name: /log in/i });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            // Form should not submit without required fields
            expect(mockAxiosInstance.post).not.toHaveBeenCalled();
            expect(screen.getByRole('alert')).toHaveTextContent(/required/i);
        });

        it('validates email format', async () => {
            await act(async () => {
                render(<LoginPage />);
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
            expect(mockAxiosInstance.post).not.toHaveBeenCalled();
            expect(screen.getByRole('alert')).toHaveTextContent(/valid email/i);
        });
    });

    describe('Error Handling', () => {
        it('displays error message on login failure', async () => {
            mockAxiosInstance.post.mockRejectedValueOnce(new Error('Login failed'));

            await act(async () => {
                render(<LoginPage />);
            });

            const emailInput = screen.getByLabelText(/email/i);
            const passwordInput = screen.getByLabelText(/password/i);
            const submitButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            await waitFor(() => {
                expect(screen.getByRole('alert')).toHaveTextContent(/login failed/i);
            });
        });

        it('handles network errors gracefully', async () => {
            mockAxiosInstance.post.mockRejectedValueOnce(new Error('Network Error'));

            await act(async () => {
                render(<LoginPage />);
            });

            const emailInput = screen.getByLabelText(/email/i);
            const passwordInput = screen.getByLabelText(/password/i);
            const submitButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordInput, { target: { value: 'password123' } });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            await waitFor(() => {
                expect(screen.getByRole('alert')).toHaveTextContent(/network error/i);
            });
        });
    });

    describe('Form State Management', () => {
        it('updates form fields on user input', async () => {
            await act(async () => {
                render(<LoginPage />);
            });

            const emailInput = screen.getByLabelText(/email/i);
            const passwordInput = screen.getByLabelText(/password/i);

            fireEvent.change(emailInput, { target: { value: 'new@example.com' } });
            fireEvent.change(passwordInput, { target: { value: 'newpassword' } });

            expect(emailInput).toHaveValue('new@example.com');
            expect(passwordInput).toHaveValue('newpassword');
        });

        it('clears form fields after successful submission', async () => {
            mockAxiosInstance.post.mockResolvedValueOnce({ data: { success: true } });

            await act(async () => {
                render(<LoginPage />);
            });

            const emailInput = screen.getByLabelText(/email/i);
            const passwordInput = screen.getByLabelText(/password/i);
            const submitButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordInput, { target: { value: 'password123' } });

            await act(async () => {
                await userEvent.click(submitButton);
            });

            await waitFor(() => {
                expect(emailInput).toHaveValue('');
                expect(passwordInput).toHaveValue('');
            });
        });
    });
}); 