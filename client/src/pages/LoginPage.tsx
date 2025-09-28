import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { H1, Body } from "../components/ui/typography";
import { PageContainer, PageHeader } from "../components/ui/layout";
import React, { Fragment, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FormField, useField } from '../hooks/useField';
import axiosInstance from "../utils/axiosInstance";

export default function LoginPage() {
    const email = useField("text", "" as string)
    const password = useField("password", "" as string)
    const navigate = useNavigate()
    const [error, setError] = useState<string | null>(null);

    const validateEmail = (email: string) => {
        // Simple email regex
        return /^\S+@\S+\.\S+$/.test(email);
    };

    const handleLogin = (email: FormField<string>, password: FormField<string>) => {
        setError(null);
        if (!email.value || !password.value) {
            setError('Email and password are required.');
            return;
        }
        if (!validateEmail(email.value)) {
            setError('Please enter a valid email address.');
            return;
        }
        const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
        const newUser = {
            "email": email.value,
            "password": password.value
        }
        axiosInstance.post(`${VITE_API_ENDPOINT}api/auth/login`, newUser)
            .then(() => {
                email.setEmpty()
                password.setEmpty()
                setError(null);
                navigate('/')
            })
            .catch(error => {
                setError(error.message || 'Login failed');
                console.log(error);
            });
    }

    const handleLogout = () => {
        const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
        axiosInstance.post(`${VITE_API_ENDPOINT}api/auth/logout`)
            .then(response => {
                console.log(response);
            })
            .catch(error => console.log(error));
    }

    return (
        <PageContainer>
            <PageHeader>
                <H1>Login</H1>
                <Body className="text-[#6B7280]">
                    Sign in to access your budgeting dashboard
                </Body>
            </PageHeader>

            <div className="w-full !max-w-[28rem] mx-auto">
                <div className="bg-white rounded-xl border border-[#E0E0E0] p-8 shadow-sm">
                    <div className="space-y-6">
                        <div className="space-y-3">
                            <Label htmlFor="login-email-input" className="text-sm font-medium text-[#374151]">
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
                            <Label htmlFor="login-password-input" className="text-sm font-medium text-[#374151]">
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
                        <div className="flex space-x-3 pt-2">
                            <Button
                                onClick={() => handleLogin(email, password)}
                                className="flex-1"
                            >
                                Log In
                            </Button>
                            <Button
                                onClick={handleLogout}
                                variant="secondary"
                                className="flex-1"
                            >
                                Log Out
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </PageContainer>
    )
}
