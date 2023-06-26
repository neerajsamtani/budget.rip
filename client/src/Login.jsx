import React, { Fragment, useState } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import axiosInstance from "./axiosInstance";

export default function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')

    const handleUsernameChange = (event) => {
        setUsername(event.target.value)
    }
    const handlePasswordChange = (event) => {
        setPassword(event.target.value)
    }

    const handleLogin = (username, password) => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        var newUser = {
            "username": username,
            "password": password
        }
        console.log(newUser);
        axiosInstance.post(`${REACT_APP_API_ENDPOINT}api/auth/login`, newUser)
            .then(response => {
                console.log(response);
            })
            .then(() => {
                setUsername('');
                setPassword('');
            })
            .catch(error => console.log(error));
    }

    return (
        <Fragment>
            <Form>
                <Form.Group className="mb-3">
                    <Form.Label>Username:</Form.Label>
                    <Form.Control type="text" value={username} onChange={handleUsernameChange} />
                </Form.Group>
                <Form.Group className="mb-3">
                    <Form.Label>Password:</Form.Label>
                    <Form.Control type="text" value={password} onChange={handlePasswordChange} />
                </Form.Group>
                <Button onClick={() => handleLogin(username, password)} variant="primary">Submit</Button>
            </Form>
        </Fragment>
    )
}