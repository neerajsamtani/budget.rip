import React from "react";
import { ToastContainer, Toast } from 'react-bootstrap';

type Notification = {
    heading: string,
    message: string,
    showNotification: boolean,
}

interface NotificationProps {
    notification: Notification,
    setNotification: (notification: Notification) => void
}

export default function Notification({ notification, setNotification }: NotificationProps) {

    const toggleShowNotification = () => {
        setNotification({
            ...notification,
            showNotification: !notification.showNotification
        })
    }

    return (
        <div className="fixed-top">
            <ToastContainer className="p-3" position='top-end' style={{ zIndex: 1 }}>
                <Toast show={notification.showNotification} onClose={toggleShowNotification} delay={3500} autohide>
                    <Toast.Header>
                        <strong className="me-auto">{notification.heading}</strong>
                    </Toast.Header>
                    <Toast.Body>{notification.message}</Toast.Body>
                </Toast>
            </ToastContainer>
        </div>
    )
}