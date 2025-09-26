import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
        <Fragment>
            <div className="space-y-4 max-w-md mx-auto p-6">
                <div className="space-y-2">
                    <Label htmlFor="login-email-input">Email:</Label>
                    <Input id="login-email-input" value={email.value} onChange={email.onChange} type={email.type} />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="login-password-input">Password:</Label>
                    <Input id="login-password-input" value={password.value} onChange={password.onChange} type={password.type} />
                </div>
                {error && <div role="alert" className="text-red-500 text-sm">{error}</div>}
                <div className="flex space-x-2">
                    <Button onClick={() => handleLogin(email, password)}>Log In</Button>
                    <Button onClick={handleLogout} variant="secondary">Log Out</Button>
                </div>
            </div>
        </Fragment>
    )
}
