import React from "react";
import { ToastContainer, Toast } from 'react-bootstrap';

export default function Notification({ notification, setNotification }) {

    const toggleShowNotification = () => {
        setNotification({
            ...notification,
            showNotification: !notification.showNotification
        })
    }

    return (
        <ToastContainer className="p-3" position='top-end'>
            <Toast show={notification.showNotification} onClose={toggleShowNotification} delay={3500} autohide>
                <Toast.Header>
                    <strong className="me-auto">{notification.heading}</strong>
                </Toast.Header>
                <Toast.Body>{notification.message}</Toast.Body>
            </Toast>
        </ToastContainer>
    )
}