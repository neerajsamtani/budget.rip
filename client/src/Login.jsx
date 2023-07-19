import React, { Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import axiosInstance from "./axiosInstance";
import { useField } from './hooks/useField';

export default function Login() {
    const username = useField("text")
    const password = useField("password")
    const navigate = useNavigate()

    const handleLogin = (username, password) => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        var newUser = {
            "username": username.value,
            "password": password.value
        }
        axiosInstance.post(`${REACT_APP_API_ENDPOINT}api/auth/login`, newUser)
            .then(() => {
                username.setEmpty()
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
                    <Form.Label>Username:</Form.Label>
                    <Form.Control value={username.value} onChange={username.onChange} type={username.type} />
                </Form.Group>
                <Form.Group className="mb-3">
                    <Form.Label>Password:</Form.Label>
                    <Form.Control value={password.value} onChange={password.onChange} type={password.type} />
                </Form.Group>
                <Button onClick={() => handleLogin(username, password)} variant="primary">Log In</Button>
                <Button onClick={handleLogout} variant="primary">Log Out</Button>
            </Form>
        </Fragment>
    )
}
