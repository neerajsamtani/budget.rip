import { fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { mockAxiosInstance, render, screen } from '../../utils/test-utils';
import EventHintsSettingsPage from '../EventHintsSettingsPage';

// Mock Sonner toast
jest.mock('sonner', () => ({
    toast: Object.assign(jest.fn(), {
        success: jest.fn(),
        error: jest.fn(),
    }),
}));

// Mock window.confirm for delete confirmations
const mockConfirm = jest.fn();
window.confirm = mockConfirm;

const mockCategories = [
    { id: 'cat_1', name: 'Dining' },
    { id: 'cat_2', name: 'Entertainment' },
    { id: 'cat_3', name: 'Subscription' },
];

const mockHints = [
    {
        id: 'hint_1',
        name: 'Spotify Subscription',
        cel_expression: 'description.contains("Spotify")',
        prefill_name: 'Spotify',
        prefill_category_id: 'cat_3',
        prefill_category: 'Subscription',
        is_active: true,
        display_order: 0,
    },
    {
        id: 'hint_2',
        name: 'Transfer Detection',
        cel_expression: 'sum(amount) == 0',
        prefill_name: 'Transfer',
        prefill_category_id: null,
        prefill_category: null,
        is_active: false,
        display_order: 1,
    },
];

const setupMocks = (hints = mockHints, categories = mockCategories) => {
    mockAxiosInstance.get.mockImplementation((url: string) => {
        if (url.includes('api/event-hints')) {
            return Promise.resolve({ data: { data: hints } });
        }
        if (url.includes('api/categories')) {
            return Promise.resolve({ data: { data: categories } });
        }
        return Promise.reject(new Error('Unknown URL'));
    });
};

describe('EventHintsSettingsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockConfirm.mockReturnValue(true);
        setupMocks();
    });

    describe('Rendering', () => {
        it('renders page header and description', async () => {
            render(<EventHintsSettingsPage />);

            expect(screen.getByText('Event Hints')).toBeInTheDocument();
            expect(screen.getByText(/Configure rules to automatically prefill/)).toBeInTheDocument();
        });

        it('shows empty state when no hints exist', async () => {
            setupMocks([]);
            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('No event hints configured yet.')).toBeInTheDocument();
            });
        });

        it('renders hints list when hints exist', async () => {
            // Use mockResolvedValueOnce for each expected call
            mockAxiosInstance.get
                .mockResolvedValueOnce({ data: { data: mockHints } })
                .mockResolvedValueOnce({ data: { data: mockCategories } });

            render(<EventHintsSettingsPage />);

            // Wait for hints to load - use getAllBy because both mobile and desktop layouts render
            await waitFor(() => {
                expect(screen.getAllByText(/Spotify Subscription/).length).toBeGreaterThan(0);
            });
            expect(screen.getAllByText(/Transfer Detection/).length).toBeGreaterThan(0);
        });

        it('renders CEL expression help section', async () => {
            setupMocks([]);
            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('CEL Expression Examples')).toBeInTheDocument();
            });
        });
    });

    describe('Creating Hints', () => {
        beforeEach(() => {
            setupMocks([]);
        });

        it('shows create form when Add New Hint button is clicked', async () => {
            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Add New Hint')).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('Add New Hint'));

            expect(screen.getByLabelText('Rule Name *')).toBeInTheDocument();
            expect(screen.getByLabelText('CEL Expression *')).toBeInTheDocument();
            expect(screen.getByLabelText('Prefill Event Name *')).toBeInTheDocument();
        });

        it('hides create form when Cancel is clicked', async () => {
            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Add New Hint')).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('Add New Hint'));
            expect(screen.getByLabelText('Rule Name *')).toBeInTheDocument();

            await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

            await waitFor(() => {
                expect(screen.queryByLabelText('Rule Name *')).not.toBeInTheDocument();
            });
        });

        it('creates a new hint when form is submitted', async () => {
            mockAxiosInstance.post.mockResolvedValue({
                data: { data: { id: 'hint_3', name: 'New Hint' } },
            });

            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Add New Hint')).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('Add New Hint'));

            fireEvent.change(screen.getByLabelText('Rule Name *'), {
                target: { value: 'New Hint' },
            });
            fireEvent.change(screen.getByLabelText('CEL Expression *'), {
                target: { value: 'amount > 50' },
            });
            fireEvent.change(screen.getByLabelText('Prefill Event Name *'), {
                target: { value: 'Large Purchase' },
            });

            await userEvent.click(screen.getByRole('button', { name: /save/i }));

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    'api/event-hints',
                    expect.objectContaining({
                        name: 'New Hint',
                        cel_expression: 'amount > 50',
                        prefill_name: 'Large Purchase',
                    })
                );
            });
        });
    });

    describe('Editing Hints', () => {
        it('shows edit form when edit button is clicked', async () => {
            setupMocks();
            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getAllByText(/Spotify Subscription/).length).toBeGreaterThan(0);
            });

            // Click the first edit button (there are 2 per hint - mobile and desktop)
            const editButtons = screen.getAllByRole('button', { name: '' }).filter(
                btn => btn.querySelector('svg.lucide-pencil')
            );
            await userEvent.click(editButtons[0]);

            // Verify edit form is displayed - look for the form labels
            expect(screen.getByLabelText('Rule Name *')).toBeInTheDocument();
            expect(screen.getByLabelText('CEL Expression *')).toBeInTheDocument();
        });

        it('updates hint when edit form is submitted', async () => {
            setupMocks();
            mockAxiosInstance.put.mockResolvedValue({
                data: { data: { ...mockHints[0], name: 'Updated Hint' } },
            });

            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getAllByText(/Spotify Subscription/).length).toBeGreaterThan(0);
            });

            const editButtons = screen.getAllByRole('button', { name: '' }).filter(
                btn => btn.querySelector('svg.lucide-pencil')
            );
            await userEvent.click(editButtons[0]);

            // Get the first name input with the current value
            const nameInputs = screen.getAllByDisplayValue('Spotify Subscription');
            fireEvent.change(nameInputs[0], { target: { value: 'Updated Hint' } });

            // Click the first Save button (there might be multiple in mobile/desktop layouts)
            const saveButtons = screen.getAllByRole('button', { name: /save/i });
            await userEvent.click(saveButtons[0]);

            await waitFor(() => {
                expect(mockAxiosInstance.put).toHaveBeenCalledWith(
                    'api/event-hints/hint_1',
                    expect.objectContaining({ name: 'Updated Hint' })
                );
            });
        });
    });

    describe('Deleting Hints', () => {
        it('deletes hint after confirmation', async () => {
            setupMocks();
            mockAxiosInstance.delete.mockResolvedValue({ data: { success: true } });

            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getAllByText(/Spotify Subscription/).length).toBeGreaterThan(0);
            });

            const deleteButtons = screen.getAllByRole('button', { name: '' }).filter(
                btn => btn.querySelector('svg.lucide-trash-2')
            );
            await userEvent.click(deleteButtons[0]);

            expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to delete this hint?');

            await waitFor(() => {
                expect(mockAxiosInstance.delete).toHaveBeenCalledWith('api/event-hints/hint_1');
            });
        });

        it('does not delete hint when confirmation is cancelled', async () => {
            setupMocks();
            mockConfirm.mockReturnValue(false);

            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getAllByText(/Spotify Subscription/).length).toBeGreaterThan(0);
            });

            const deleteButtons = screen.getAllByRole('button', { name: '' }).filter(
                btn => btn.querySelector('svg.lucide-trash-2')
            );
            await userEvent.click(deleteButtons[0]);

            expect(mockConfirm).toHaveBeenCalled();
            expect(mockAxiosInstance.delete).not.toHaveBeenCalled();
        });
    });

    describe('CEL Validation', () => {
        beforeEach(() => {
            setupMocks([]);
        });

        it('validates CEL expression when Validate button is clicked', async () => {
            mockAxiosInstance.post.mockResolvedValue({
                data: { is_valid: true },
            });

            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Add New Hint')).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('Add New Hint'));

            const celInput = screen.getByLabelText('CEL Expression *');
            fireEvent.change(celInput, { target: { value: 'amount > 100' } });

            // Wait for the Validate button to be enabled
            await waitFor(() => {
                const validateBtn = screen.getByRole('button', { name: /validate/i });
                expect(validateBtn).not.toBeDisabled();
            });

            await userEvent.click(screen.getByRole('button', { name: /validate/i }));

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    'api/event-hints/validate',
                    { cel_expression: 'amount > 100' }
                );
            });
        });

        it('validates and handles invalid CEL expressions', async () => {
            mockAxiosInstance.post.mockResolvedValue({
                data: { is_valid: false, error: 'Syntax error at position 5' },
            });

            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getByText('Add New Hint')).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('Add New Hint'));

            fireEvent.change(screen.getByLabelText('CEL Expression *'), {
                target: { value: 'invalid expression' },
            });

            // Wait for the Validate button to be enabled
            await waitFor(() => {
                const validateBtn = screen.getByRole('button', { name: /validate/i });
                expect(validateBtn).not.toBeDisabled();
            });

            await userEvent.click(screen.getByRole('button', { name: /validate/i }));

            // Verify the validation API was called with the expression
            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    'api/event-hints/validate',
                    { cel_expression: 'invalid expression' }
                );
            });
        });
    });

    describe('Active Toggle', () => {
        it('toggles hint active state', async () => {
            setupMocks();
            mockAxiosInstance.put.mockResolvedValue({
                data: { data: { ...mockHints[0], is_active: false } },
            });

            render(<EventHintsSettingsPage />);

            await waitFor(() => {
                expect(screen.getAllByText(/Spotify Subscription/).length).toBeGreaterThan(0);
            });

            // Find the switch for the first hint - there are multiple switches
            const switches = screen.getAllByRole('switch');
            expect(switches[0]).toHaveAttribute('data-state', 'checked');

            await userEvent.click(switches[0]);

            await waitFor(() => {
                expect(mockAxiosInstance.put).toHaveBeenCalledWith(
                    'api/event-hints/hint_1',
                    expect.objectContaining({ is_active: false })
                );
            });
        });
    });
});
