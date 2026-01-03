import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen, mockAxiosInstance, waitFor } from '../../../utils/test-utils';
import EventHintsSettings from '../EventHintsSettings';

// Mock event hints data
const mockHints = [
    {
        id: 'hint_1',
        name: 'Spotify Subscription',
        cel_expression: 'description.contains("spotify")',
        prefill_name: 'Spotify',
        prefill_category_id: 'cat_subscription',
        prefill_category: 'Subscription',
        is_active: true,
    },
    {
        id: 'hint_2',
        name: 'Uber Rides',
        cel_expression: 'description.contains("uber")',
        prefill_name: 'Uber',
        prefill_category_id: 'cat_transit',
        prefill_category: 'Transit',
        is_active: true,
    },
    {
        id: 'hint_3',
        name: 'Whole Foods',
        cel_expression: 'description.contains("whole foods")',
        prefill_name: 'Groceries',
        prefill_category_id: 'cat_groceries',
        prefill_category: 'Groceries',
        is_active: false,
    },
];

const mockCategories = [
    { id: 'cat_subscription', name: 'Subscription' },
    { id: 'cat_transit', name: 'Transit' },
    { id: 'cat_groceries', name: 'Groceries' },
];

// Mock Sonner toast
jest.mock('sonner', () => ({
    toast: Object.assign(jest.fn(), {
        success: jest.fn(),
        error: jest.fn(),
    }),
}));

describe('EventHintsSettings', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Set up default successful mock responses
        (mockAxiosInstance.get as jest.Mock).mockImplementation((url: string) => {
            if (url.includes('event-hints')) {
                return Promise.resolve({ data: { data: mockHints } });
            }
            if (url.includes('categories')) {
                return Promise.resolve({ data: { data: mockCategories } });
            }
            return Promise.reject(new Error('Unknown URL'));
        });
        (mockAxiosInstance.post as jest.Mock).mockResolvedValue({
            data: { data: { id: 'hint_new', name: 'New Hint' } }
        });
        (mockAxiosInstance.put as jest.Mock).mockResolvedValue({
            data: { data: { id: 'hint_1', name: 'Updated Hint' } }
        });
        (mockAxiosInstance.delete as jest.Mock).mockResolvedValue({
            data: { message: 'Hint deleted' }
        });
    });

    describe('Rendering', () => {
        it('add new hint button is rendered', () => {
            render(<EventHintsSettings />);
            expect(screen.getByRole('button', { name: /add new hint/i })).toBeInTheDocument();
        });

        it('hints list is rendered after loading', async () => {
            render(<EventHintsSettings />);

            // Hints appear in both mobile and desktop views
            await waitFor(() => {
                expect(screen.getAllByText('Spotify Subscription').length).toBeGreaterThan(0);
            });

            expect(screen.getAllByText('Uber Rides').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Whole Foods').length).toBeGreaterThan(0);
        });

        it('empty state is rendered when no hints', async () => {
            (mockAxiosInstance.get as jest.Mock).mockImplementation((url: string) => {
                if (url.includes('event-hints')) {
                    return Promise.resolve({ data: { data: [] } });
                }
                if (url.includes('categories')) {
                    return Promise.resolve({ data: { data: mockCategories } });
                }
                return Promise.reject(new Error('Unknown URL'));
            });

            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getByText(/no event hints configured yet/i)).toBeInTheDocument();
            });
        });

        it('inactive hints are shown with reduced opacity', async () => {
            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Whole Foods').length).toBeGreaterThan(0);
            });

            // The inactive hint row should have opacity-60 class
            const rows = screen.getAllByText('Whole Foods')[0].closest('tr') ||
                         screen.getAllByText('Whole Foods')[0].closest('div.border');
            expect(rows).toHaveClass('opacity-60');
        });
    });

    describe('Reordering Hints', () => {
        it('up and down buttons are rendered for each hint', async () => {
            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Spotify Subscription').length).toBeGreaterThan(0);
            });

            // Each hint has up/down buttons (in both mobile and desktop views)
            // We have 3 hints, each with 2 buttons, in 2 views = 12 buttons total
            // But we'll just check that the buttons exist
            const chevronUpButtons = screen.getAllByRole('button').filter(
                button => button.querySelector('svg.lucide-chevron-up')
            );
            const chevronDownButtons = screen.getAllByRole('button').filter(
                button => button.querySelector('svg.lucide-chevron-down')
            );

            expect(chevronUpButtons.length).toBeGreaterThan(0);
            expect(chevronDownButtons.length).toBeGreaterThan(0);
        });

        it('up button is disabled for first hint', async () => {
            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Spotify Subscription').length).toBeGreaterThan(0);
            });

            // Find the first hint's up buttons (both mobile and desktop)
            const allButtons = screen.getAllByRole('button');
            const upButtons = allButtons.filter(
                button => button.querySelector('svg.lucide-chevron-up')
            );

            // At least some up buttons should be disabled (first hint in each view)
            const disabledUpButtons = upButtons.filter(button => button.disabled);
            expect(disabledUpButtons.length).toBeGreaterThan(0);
        });

        it('down button is disabled for last hint', async () => {
            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Whole Foods').length).toBeGreaterThan(0);
            });

            // Find all down buttons
            const allButtons = screen.getAllByRole('button');
            const downButtons = allButtons.filter(
                button => button.querySelector('svg.lucide-chevron-down')
            );

            // At least some down buttons should be disabled (last hint in each view)
            const disabledDownButtons = downButtons.filter(button => button.disabled);
            expect(disabledDownButtons.length).toBeGreaterThan(0);
        });

        it('reorder API is called when moving hint up', async () => {
            (mockAxiosInstance.put as jest.Mock).mockResolvedValue({
                data: { data: mockHints }
            });

            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Uber Rides').length).toBeGreaterThan(0);
            });

            // Find the second hint's up button (in desktop view for simplicity)
            // We'll use the table structure to find it
            const allButtons = screen.getAllByRole('button');
            const upButtons = allButtons.filter(
                button => button.querySelector('svg.lucide-chevron-up') && !button.disabled
            );

            // Click the first enabled up button (should be the second hint)
            await userEvent.click(upButtons[0]);

            // Should call the reorder endpoint with swapped order
            await waitFor(() => {
                expect(mockAxiosInstance.put).toHaveBeenCalledWith(
                    'api/event-hints/reorder',
                    { hint_ids: ['hint_2', 'hint_1', 'hint_3'] }
                );
            });
        });

        it('reorder API is called when moving hint down', async () => {
            (mockAxiosInstance.put as jest.Mock).mockResolvedValue({
                data: { data: mockHints }
            });

            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Spotify Subscription').length).toBeGreaterThan(0);
            });

            // Find the first hint's down button
            const allButtons = screen.getAllByRole('button');
            const downButtons = allButtons.filter(
                button => button.querySelector('svg.lucide-chevron-down') && !button.disabled
            );

            // Click the first enabled down button (should be the first hint)
            await userEvent.click(downButtons[0]);

            // Should call the reorder endpoint with swapped order
            await waitFor(() => {
                expect(mockAxiosInstance.put).toHaveBeenCalledWith(
                    'api/event-hints/reorder',
                    { hint_ids: ['hint_2', 'hint_1', 'hint_3'] }
                );
            });
        });

        it('all reorder buttons are disabled while reorder is pending', async () => {
            // Create a promise that we can control
            let resolveReorder: (value: any) => void;
            const reorderPromise = new Promise((resolve) => {
                resolveReorder = resolve;
            });

            (mockAxiosInstance.put as jest.Mock).mockReturnValue(reorderPromise);

            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Spotify Subscription').length).toBeGreaterThan(0);
            });

            // Find and click a down button
            const allButtons = screen.getAllByRole('button');
            const downButtons = allButtons.filter(
                button => button.querySelector('svg.lucide-chevron-down') && !button.disabled
            );

            await userEvent.click(downButtons[0]);

            // All reorder buttons should now be disabled
            await waitFor(() => {
                const allButtonsAfter = screen.getAllByRole('button');
                const upButtons = allButtonsAfter.filter(
                    button => button.querySelector('svg.lucide-chevron-up')
                );
                const downButtonsAfter = allButtonsAfter.filter(
                    button => button.querySelector('svg.lucide-chevron-down')
                );

                // All up/down buttons should be disabled
                upButtons.forEach(button => {
                    expect(button).toBeDisabled();
                });
                downButtonsAfter.forEach(button => {
                    expect(button).toBeDisabled();
                });
            });

            // Resolve the promise to clean up
            resolveReorder!({ data: { data: mockHints } });
        });

        it('API is not called when trying to move first hint up', async () => {
            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Spotify Subscription').length).toBeGreaterThan(0);
            });

            // The first hint's up button should be disabled, so we can't click it
            // Just verify the button is disabled
            const allButtons = screen.getAllByRole('button');
            const upButtons = allButtons.filter(
                button => button.querySelector('svg.lucide-chevron-up')
            );

            const disabledUpButtons = upButtons.filter(button => button.disabled);
            expect(disabledUpButtons.length).toBeGreaterThan(0);

            // No reorder API call should have been made
            expect(mockAxiosInstance.put).not.toHaveBeenCalledWith(
                expect.stringContaining('reorder'),
                expect.anything()
            );
        });

        it('API is not called when trying to move last hint down', async () => {
            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getAllByText('Whole Foods').length).toBeGreaterThan(0);
            });

            // The last hint's down button should be disabled
            const allButtons = screen.getAllByRole('button');
            const downButtons = allButtons.filter(
                button => button.querySelector('svg.lucide-chevron-down')
            );

            const disabledDownButtons = downButtons.filter(button => button.disabled);
            expect(disabledDownButtons.length).toBeGreaterThan(0);

            // No reorder API call should have been made
            expect(mockAxiosInstance.put).not.toHaveBeenCalledWith(
                expect.stringContaining('reorder'),
                expect.anything()
            );
        });
    });

    describe('Error Handling', () => {
        it('error state is shown when loading fails', async () => {
            (mockAxiosInstance.get as jest.Mock).mockRejectedValue(new Error('Failed to load'));

            render(<EventHintsSettings />);

            await waitFor(() => {
                expect(screen.getByText(/failed to load event hints/i)).toBeInTheDocument();
            });
        });
    });
});
