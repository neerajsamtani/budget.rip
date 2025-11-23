import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";
import { FormField, useField } from '../hooks/useField';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
    const email = useField("text", "" as string)
    const password = useField("password", "" as string)
    const navigate = useNavigate()
    const location = useLocation()
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const { login } = useAuth();

    const validateEmail = (email: string) => {
        // Simple email regex
        return /^\S+@\S+\.\S+$/.test(email);
    };

    const handleLogin = async (emailField: FormField<string>, passwordField: FormField<string>) => {
        setError(null);
        if (!emailField.value || !passwordField.value) {
            setError('Email and password are required.');
            return;
        }
        if (!validateEmail(emailField.value)) {
            setError('Please enter a valid email address.');
            return;
        }

        setIsSubmitting(true);
        try {
            await login(emailField.value, passwordField.value);
            emailField.setEmpty();
            passwordField.setEmpty();
            // Redirect to the page they tried to visit, or home
            const from = location.state?.from?.pathname || '/';
            navigate(from, { replace: true });
        } catch (err: any) {
            setError(err.response?.data?.error || err.message || 'Login failed');
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <PageContainer>
            <PageHeader>
                <H1>Login</H1>
                <Body className="text-muted-foreground">
                    Sign in to access your budgeting dashboard
                </Body>
            </PageHeader>

            <div className="w-full !max-w-[28rem] mx-auto">
                <div className="bg-white rounded-xl border p-8 shadow-sm">
                    <div className="space-y-6">
                        <div className="space-y-3">
                            <Label htmlFor="login-email-input" className="text-sm font-medium text-foreground">
                                Email
                            </Label>
                            <Input
                                id="login-email-input"
                                value={email.value}
                                onChange={email.onChange}
                                type={email.type}
                                className="w-full !min-w-[250px]"
                                placeholder="Enter your email address"
                            />
                        </div>
                        <div className="space-y-3">
                            <Label htmlFor="login-password-input" className="text-sm font-medium text-foreground">
                                Password
                            </Label>
                            <Input
                                id="login-password-input"
                                value={password.value}
                                onChange={password.onChange}
                                type={password.type}
                                className="w-full !min-w-[250px]"
                                placeholder="Enter your password"
                            />
                        </div>
                        {error && (
                            <div role="alert" className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                                {error}
                            </div>
                        )}
                        <Button
                            onClick={() => handleLogin(email, password)}
                            className="w-full"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? 'Logging in...' : 'Log In'}
                        </Button>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}
