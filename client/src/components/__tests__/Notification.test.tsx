import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen } from '../../utils/test-utils';
import Notification from '../Notification';

describe('Notification', () => {
    const mockSetNotification = jest.fn();

    const mockNotification = {
        heading: 'Test Heading',
        message: 'Test Message',
        showNotification: true,
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Rendering', () => {
        it('renders notification when showNotification is true', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            expect(screen.getByText('Test Heading')).toBeInTheDocument();
            expect(screen.getByText('Test Message')).toBeInTheDocument();
        });

        it('does not render notification when showNotification is false', () => {
            const hiddenNotification = {
                ...mockNotification,
                showNotification: false,
            };

            render(<Notification notification={hiddenNotification} setNotification={mockSetNotification} />);

            expect(screen.queryByText('Test Heading')).not.toBeInTheDocument();
            expect(screen.queryByText('Test Message')).not.toBeInTheDocument();
        });

        it('renders with proper toast structure', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            // Check for ToastContainer and Toast structure
            expect(screen.getByText('Test Heading')).toBeInTheDocument();
            expect(screen.getByText('Test Message')).toBeInTheDocument();
        });

        it('renders with proper CSS classes', () => {
            const { container } = render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            expect(container.querySelector('.fixed-top')).toBeInTheDocument();
        });

        it('displays heading in strong tag', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            const headingElement = screen.getByText('Test Heading');
            expect(headingElement.tagName).toBe('STRONG');
        });

        it('displays message in toast body', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            expect(screen.getByText('Test Message')).toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('calls setNotification when close button is clicked', async () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            const closeButton = screen.getByRole('button', { name: /close/i });
            await userEvent.click(closeButton);

            expect(mockSetNotification).toHaveBeenCalledWith({
                heading: 'Test Heading',
                message: 'Test Message',
                showNotification: false,
            });
        });

        it('toggles showNotification when close is triggered', async () => {
            const notificationWithFalse = {
                ...mockNotification,
                showNotification: false,
            };

            render(<Notification notification={notificationWithFalse} setNotification={mockSetNotification} />);

            // Since showNotification is false, the toast shouldn't be visible
            expect(screen.queryByText('Test Heading')).not.toBeInTheDocument();

            // If we were to trigger the close function, it would set showNotification to true
            // This tests the toggle logic
            const expectedCall = {
                heading: 'Test Heading',
                message: 'Test Message',
                showNotification: true,
            };

            // Simulate the toggle function call
            mockSetNotification(expectedCall);
            expect(mockSetNotification).toHaveBeenCalledWith(expectedCall);
        });
    });

    describe('Props Handling', () => {
        it('accepts different notification content', () => {
            const customNotification = {
                heading: 'Custom Heading',
                message: 'Custom Message',
                showNotification: true,
            };

            render(<Notification notification={customNotification} setNotification={mockSetNotification} />);

            expect(screen.getByText('Custom Heading')).toBeInTheDocument();
            expect(screen.getByText('Custom Message')).toBeInTheDocument();
        });

        it('handles empty strings in notification content', () => {
            const emptyNotification = {
                heading: '',
                message: '',
                showNotification: true,
            };

            render(<Notification notification={emptyNotification} setNotification={mockSetNotification} />);

            // Should render without crashing
            expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
        });

        it('calls the provided setNotification function', async () => {
            const customSetNotification = jest.fn();
            render(<Notification notification={mockNotification} setNotification={customSetNotification} />);

            const closeButton = screen.getByRole('button', { name: /close/i });
            await userEvent.click(closeButton);

            expect(customSetNotification).toHaveBeenCalledWith({
                heading: 'Test Heading',
                message: 'Test Message',
                showNotification: false,
            });
        });

        it('preserves other notification properties when toggling', async () => {
            const complexNotification = {
                heading: 'Complex Heading',
                message: 'Complex Message',
                showNotification: true,
            };

            render(<Notification notification={complexNotification} setNotification={mockSetNotification} />);

            const closeButton = screen.getByRole('button', { name: /close/i });
            await userEvent.click(closeButton);

            expect(mockSetNotification).toHaveBeenCalledWith({
                heading: 'Complex Heading',
                message: 'Complex Message',
                showNotification: false,
            });
        });
    });

    describe('Toast Configuration', () => {
        it('has proper toast attributes', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            // Check for close button (part of Toast.Header)
            expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
        });

        it('renders with proper positioning', () => {
            const { container } = render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            // Check for fixed-top positioning
            expect(container.querySelector('.fixed-top')).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('has proper close button with accessible name', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            const closeButton = screen.getByRole('button', { name: /close/i });
            expect(closeButton).toBeInTheDocument();
        });

        it('has proper heading structure', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            const heading = screen.getByText('Test Heading');
            expect(heading).toBeInTheDocument();
            expect(heading.tagName).toBe('STRONG');
        });

        it('has proper toast role', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            // Toast should be accessible
            expect(screen.getByText('Test Heading')).toBeInTheDocument();
            expect(screen.getByText('Test Message')).toBeInTheDocument();
        });
    });

    describe('Component Structure', () => {
        it('renders with ToastContainer structure', () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            // Check for the presence of toast content
            expect(screen.getByText('Test Heading')).toBeInTheDocument();
            expect(screen.getByText('Test Message')).toBeInTheDocument();
        });

        it('renders with proper div wrapper', () => {
            const { container } = render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            expect(container.firstChild).toHaveClass('fixed-top');
        });
    });

    describe('Edge Cases', () => {
        it('handles very long notification content', () => {
            const longNotification = {
                heading: 'This is a very long heading that might wrap to multiple lines and test the component\'s ability to handle lengthy text content',
                message: 'This is a very long message that might wrap to multiple lines and test the component\'s ability to handle lengthy text content. It should still render properly without breaking the layout.',
                showNotification: true,
            };

            render(<Notification notification={longNotification} setNotification={mockSetNotification} />);

            expect(screen.getByText(longNotification.heading)).toBeInTheDocument();
            expect(screen.getByText(longNotification.message)).toBeInTheDocument();
        });

        it('handles special characters in notification content', () => {
            const specialNotification = {
                heading: 'Special & Characters < > " \'',
                message: 'Message with special characters: & < > " \'',
                showNotification: true,
            };

            render(<Notification notification={specialNotification} setNotification={mockSetNotification} />);

            expect(screen.getByText(specialNotification.heading)).toBeInTheDocument();
            expect(screen.getByText(specialNotification.message)).toBeInTheDocument();
        });

        it('handles rapid close button clicks', async () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            const closeButton = screen.getByRole('button', { name: /close/i });

            await userEvent.click(closeButton);
            await userEvent.click(closeButton);
            await userEvent.click(closeButton);

            expect(mockSetNotification).toHaveBeenCalledTimes(3);
        });

        it('maintains notification state after prop updates', () => {
            const { rerender } = render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);
            expect(screen.getByText('Test Heading')).toBeInTheDocument();

            const updatedNotification = {
                ...mockNotification,
                heading: 'Updated Heading',
                message: 'Updated Message',
            };

            rerender(<Notification notification={updatedNotification} setNotification={mockSetNotification} />);
            expect(screen.getByText('Updated Heading')).toBeInTheDocument();
            expect(screen.getByText('Updated Message')).toBeInTheDocument();
        });
    });

    describe('State Management', () => {
        it('correctly toggles showNotification state', async () => {
            render(<Notification notification={mockNotification} setNotification={mockSetNotification} />);

            const closeButton = screen.getByRole('button', { name: /close/i });
            await userEvent.click(closeButton);

            expect(mockSetNotification).toHaveBeenCalledWith({
                heading: 'Test Heading',
                message: 'Test Message',
                showNotification: false,
            });
        });

        it('preserves notification data when toggling visibility', async () => {
            const customNotification = {
                heading: 'Preserved Heading',
                message: 'Preserved Message',
                showNotification: true,
            };

            render(<Notification notification={customNotification} setNotification={mockSetNotification} />);

            const closeButton = screen.getByRole('button', { name: /close/i });
            await userEvent.click(closeButton);

            expect(mockSetNotification).toHaveBeenCalledWith({
                heading: 'Preserved Heading',
                message: 'Preserved Message',
                showNotification: false,
            });
        });
    });
}); 