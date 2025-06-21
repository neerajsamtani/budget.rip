import React, { Fragment } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { useNavigate } from 'react-router-dom';
import { FormField, useField } from '../hooks/useField';
import axiosInstance from "../utils/axiosInstance";

export default function LoginPage() {
    const email = useField("text", "" as string)
    const password = useField("password", "" as string)
    const navigate = useNavigate()

    const handleLogin = (email: FormField<string>, password: FormField<string>) => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        var newUser = {
            "email": email.value,
            "password": password.value
        }
        axiosInstance.post(`${REACT_APP_API_ENDPOINT}api/auth/login`, newUser)
            .then(() => {
                email.setEmpty()
                password.setEmpty()
                navigate('/')
            })
            .catch(error => console.log(error));
    }

    const handleLogout = () => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axiosInstance.post(`${REACT_APP_API_ENDPOINT}api/auth/logout`)
            .then(response => {
                console.log(response);
            })
            .catch(error => console.log(error));
    }

    return (
        <Fragment>
            <Form>
                <Form.Group className="mb-3">
                    <Form.Label htmlFor="login-email-input">Email:</Form.Label>
                    <Form.Control id="login-email-input" value={email.value} onChange={email.onChange} type={email.type} />
                </Form.Group>
                <Form.Group className="mb-3">
                    <Form.Label htmlFor="login-password-input">Password:</Form.Label>
                    <Form.Control id="login-password-input" value={password.value} onChange={password.onChange} type={password.type} />
                </Form.Group>
                <Button onClick={() => handleLogin(email, password)} variant="primary">Log In</Button>
                <Button onClick={handleLogout} variant="primary">Log Out</Button>
            </Form>
        </Fragment>
    )
}
