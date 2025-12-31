import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen, mockAxiosInstance, waitFor } from '../../../utils/test-utils';
import CategoriesSettings from '../CategoriesSettings';

// Mock categories data
const mockCategories = [
    { id: 'cat_dining', name: 'Dining', is_active: true },
    { id: 'cat_entertainment', name: 'Entertainment', is_active: true },
    { id: 'cat_groceries', name: 'Groceries', is_active: true },
];

// Mock Sonner toast
jest.mock('sonner', () => ({
    toast: Object.assign(jest.fn(), {
        success: jest.fn(),
        error: jest.fn(),
    }),
}));

describe('CategoriesSettings', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Set up default successful mock responses
        (mockAxiosInstance.get as jest.Mock).mockResolvedValue({
            data: { data: mockCategories }
        });
        (mockAxiosInstance.post as jest.Mock).mockResolvedValue({
            data: { data: { id: 'cat_new', name: 'New Category', is_active: true } }
        });
        (mockAxiosInstance.put as jest.Mock).mockResolvedValue({
            data: { data: { id: 'cat_dining', name: 'Updated Dining', is_active: true } }
        });
        (mockAxiosInstance.delete as jest.Mock).mockResolvedValue({
            data: { message: 'Category deleted' }
        });
    });

    describe('Rendering', () => {
        it('renders add new category button', () => {
            render(<CategoriesSettings />);
            expect(screen.getByRole('button', { name: /add new category/i })).toBeInTheDocument();
        });

        it('renders categories list after loading', async () => {
            render(<CategoriesSettings />);

            // Categories appear in both mobile and desktop views, so use getAllByText
            await waitFor(() => {
                expect(screen.getAllByText('Dining').length).toBeGreaterThan(0);
            });

            expect(screen.getAllByText('Entertainment').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Groceries').length).toBeGreaterThan(0);
        });

        it('renders empty state when no categories', async () => {
            (mockAxiosInstance.get as jest.Mock).mockResolvedValue({ data: { data: [] } });

            render(<CategoriesSettings />);

            await waitFor(() => {
                expect(screen.getByText(/no categories configured yet/i)).toBeInTheDocument();
            });
        });
    });

    describe('Create Category', () => {
        it('shows create form when add button is clicked', async () => {
            render(<CategoriesSettings />);

            const addButton = screen.getByRole('button', { name: /add new category/i });
            await userEvent.click(addButton);

            expect(screen.getByLabelText(/category name/i)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        });

        it('hides add button when create form is visible', async () => {
            render(<CategoriesSettings />);

            const addButton = screen.getByRole('button', { name: /add new category/i });
            await userEvent.click(addButton);

            expect(screen.queryByRole('button', { name: /add new category/i })).not.toBeInTheDocument();
        });

        it('creates category on form submit', async () => {
            render(<CategoriesSettings />);

            // Open create form
            await userEvent.click(screen.getByRole('button', { name: /add new category/i }));

            // Fill in the name
            const nameInput = screen.getByLabelText(/category name/i);
            await userEvent.type(nameInput, 'New Category');

            // Submit
            await userEvent.click(screen.getByRole('button', { name: /save/i }));

            await waitFor(() => {
                expect(mockAxiosInstance.post).toHaveBeenCalledWith(
                    'api/categories',
                    { name: 'New Category' }
                );
            });
        });

        it('cancels create form when cancel is clicked', async () => {
            render(<CategoriesSettings />);

            // Open create form
            await userEvent.click(screen.getByRole('button', { name: /add new category/i }));
            expect(screen.getByLabelText(/category name/i)).toBeInTheDocument();

            // Cancel
            await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

            // Form should be hidden
            expect(screen.queryByLabelText(/category name/i)).not.toBeInTheDocument();
            // Add button should be visible again
            expect(screen.getByRole('button', { name: /add new category/i })).toBeInTheDocument();
        });
    });

    describe('Error Handling', () => {
        it('shows error state when loading fails', async () => {
            (mockAxiosInstance.get as jest.Mock).mockRejectedValue(new Error('Failed to load'));

            render(<CategoriesSettings />);

            await waitFor(() => {
                expect(screen.getByText(/failed to load categories/i)).toBeInTheDocument();
            });
        });
    });

    describe('Accessibility', () => {
        it('has proper form labels in create form', async () => {
            render(<CategoriesSettings />);

            await userEvent.click(screen.getByRole('button', { name: /add new category/i }));

            const input = screen.getByLabelText(/category name/i);
            expect(input).toHaveAttribute('id', 'category-name');
        });

        it('has save and cancel buttons in form', async () => {
            render(<CategoriesSettings />);

            await userEvent.click(screen.getByRole('button', { name: /add new category/i }));

            expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        });
    });
});
