import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen, waitFor } from '../../utils/test-utils';
import LoginPage from '../LoginPage';

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
        it('renders login form with all required elements', () => {
            render(<LoginPage />);

            expect(screen.getByLabelText('Email:')).toBeInTheDocument();
            expect(screen.getByLabelText('Password:')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
        });

        it('renders form fields with correct types', () => {
            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:') as HTMLInputElement;
            const passwordField = screen.getByLabelText('Password:') as HTMLInputElement;

            expect(emailField.type).toBe('text');
            expect(passwordField.type).toBe('password');
        });

        it('renders form fields with empty initial values', () => {
            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:') as HTMLInputElement;
            const passwordField = screen.getByLabelText('Password:') as HTMLInputElement;

            expect(emailField.value).toBe('');
            expect(passwordField.value).toBe('');
        });
    });

    describe('User Interactions', () => {
        it('allows typing in email field', () => {
            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:');
            fireEvent.change(emailField, { target: { value: 'test@example.com' } });

            expect(emailField).toHaveValue('test@example.com');
        });

        it('allows typing in password field', () => {
            render(<LoginPage />);

            const passwordField = screen.getByLabelText('Password:');
            fireEvent.change(passwordField, { target: { value: 'password123' } });

            expect(passwordField).toHaveValue('password123');
        });

        it('calls login API when Log In button is clicked', async () => {
            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:');
            const passwordField = screen.getByLabelText('Password:');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await userEvent.click(loginButton);

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
            render(<LoginPage />);

            const logoutButton = screen.getByRole('button', { name: /log out/i });
            await userEvent.click(logoutButton);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/auth/logout')
                );
            });
        });

        it('navigates to home page after successful login', async () => {
            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:');
            const passwordField = screen.getByLabelText('Password:');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await userEvent.click(loginButton);

            await waitFor(() => {
                expect(mockNavigate).toHaveBeenCalledWith('/');
            });
        });

        it('clears form fields after successful login', async () => {
            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:');
            const passwordField = screen.getByLabelText('Password:');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await userEvent.click(loginButton);

            await waitFor(() => {
                expect(emailField).toHaveValue('');
                expect(passwordField).toHaveValue('');
            });
        });
    });

    describe('Error Handling', () => {
        it('handles login API error gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.post.mockRejectedValue(new Error('Login failed'));

            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:');
            const passwordField = screen.getByLabelText('Password:');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await userEvent.click(loginButton);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });

            consoleSpy.mockRestore();
        });

        it('handles logout API error gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            mockAxiosInstance.post.mockRejectedValueOnce(new Error('Logout failed'));

            render(<LoginPage />);

            const logoutButton = screen.getByRole('button', { name: /log out/i });
            await userEvent.click(logoutButton);

            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
            });

            consoleSpy.mockRestore();
        });

        it('does not navigate on login error', async () => {
            mockAxiosInstance.post.mockRejectedValue(new Error('Login failed'));

            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:');
            const passwordField = screen.getByLabelText('Password:');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'password123' } });
            await userEvent.click(loginButton);

            await waitFor(() => {
                expect(mockNavigate).not.toHaveBeenCalled();
            });
        });
    });

    describe('Accessibility', () => {
        it('has proper form labels', () => {
            render(<LoginPage />);

            expect(screen.getByLabelText('Email:')).toBeInTheDocument();
            expect(screen.getByLabelText('Password:')).toBeInTheDocument();
        });

        it('has proper button labels', () => {
            render(<LoginPage />);

            expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
        });

        it('has proper form structure', () => {
            render(<LoginPage />);

            // Check that form elements are present
            expect(screen.getByLabelText('Email:')).toBeInTheDocument();
            expect(screen.getByLabelText('Password:')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
        });
    });

    describe('Form Validation', () => {
        it('allows empty fields to be submitted', async () => {
            render(<LoginPage />);

            const loginButton = screen.getByRole('button', { name: /log in/i });
            await userEvent.click(loginButton);

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    expect.stringContaining('api/auth/login'),
                    {
                        email: '',
                        password: ''
                    }
                );
            });
        });

        it('handles special characters in email and password', async () => {
            render(<LoginPage />);

            const emailField = screen.getByLabelText('Email:');
            const passwordField = screen.getByLabelText('Password:');
            const loginButton = screen.getByRole('button', { name: /log in/i });

            fireEvent.change(emailField, { target: { value: 'test+tag@example.com' } });
            fireEvent.change(passwordField, { target: { value: 'pass@word!123' } });
            await userEvent.click(loginButton);

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
    });
}); 