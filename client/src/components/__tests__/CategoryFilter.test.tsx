import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen, mockAxiosInstance, waitFor } from '../../utils/test-utils';
import CategoryFilter from '../CategoryFilter';

// Mock categories data that matches what the API returns
const mockCategories = [
    { id: 'cat_alcohol', name: 'Alcohol' },
    { id: 'cat_dining', name: 'Dining' },
    { id: 'cat_entertainment', name: 'Entertainment' },
    { id: 'cat_groceries', name: 'Groceries' },
    { id: 'cat_hobbies', name: 'Hobbies' },
    { id: 'cat_income', name: 'Income' },
    { id: 'cat_investment', name: 'Investment' },
    { id: 'cat_medical', name: 'Medical' },
    { id: 'cat_rent', name: 'Rent' },
    { id: 'cat_shopping', name: 'Shopping' },
    { id: 'cat_subscription', name: 'Subscription' },
    { id: 'cat_transfer', name: 'Transfer' },
    { id: 'cat_transit', name: 'Transit' },
    { id: 'cat_travel', name: 'Travel' },
];

describe('CategoryFilter', () => {
    const mockSetCategory = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
        // Mock the categories API call
        (mockAxiosInstance.get as jest.Mock).mockImplementation((url: string) => {
            if (url === 'api/categories') {
                return Promise.resolve({ data: { data: mockCategories } });
            }
            return Promise.reject(new Error('Not found'));
        });
    });

    describe('Rendering', () => {
        it('renders category filter with all categories', async () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            expect(screen.getByText('Category')).toBeInTheDocument();
            expect(screen.getByText('All')).toBeInTheDocument();

            // Wait for categories to load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/categories');
            });

            // Open select to see all options
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                expect(screen.getAllByText('Entertainment').length).toBeGreaterThanOrEqual(1);
                expect(screen.getAllByText('Shopping').length).toBeGreaterThanOrEqual(1);
                expect(screen.getAllByText('Travel').length).toBeGreaterThanOrEqual(1);
            });
        });

        it('shows selected category when provided', async () => {
            render(
                <CategoryFilter
                    category="Entertainment"
                    setCategory={mockSetCategory}
                />
            );

            // Wait for categories to load and the selected value to render
            await waitFor(() => {
                expect(screen.getByText('Entertainment')).toBeInTheDocument();
            });
        });

        it('shows "All" when All category is selected', () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            expect(screen.getByText('All')).toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('calls setCategory when a category is selected', async () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            // Wait for categories to load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/categories');
            });

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(async () => {
                const entertainmentOption = screen.getByText('Entertainment');
                await userEvent.click(entertainmentOption);
            });

            expect(mockSetCategory).toHaveBeenCalledWith('Entertainment');
        });

        it('calls setCategory with "All" when All is selected', async () => {
            render(
                <CategoryFilter
                    category="Entertainment"
                    setCategory={mockSetCategory}
                />
            );

            // Wait for categories to load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/categories');
            });

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            await waitFor(() => {
                // Find the "All" option in the dropdown
                const allOptions = screen.getAllByText('All');
                expect(allOptions.length).toBeGreaterThan(0);
            });

            const allOptions = screen.getAllByText('All');
            const allOption = allOptions.find(option =>
                option.getAttribute('role') === 'option' ||
                option.closest('[role="option"]')
            ) || allOptions[allOptions.length - 1];

            await userEvent.click(allOption);

            expect(mockSetCategory).toHaveBeenCalledWith('All');
        });

        it('handles multiple category selections', async () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            // Wait for categories to load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/categories');
            });

            const trigger = screen.getByRole('combobox');

            // First selection
            await userEvent.click(trigger);
            await waitFor(async () => {
                await userEvent.click(screen.getByText('Entertainment'));
            });
            expect(mockSetCategory).toHaveBeenCalledWith('Entertainment');

            // Second selection
            await userEvent.click(trigger);
            await waitFor(async () => {
                await userEvent.click(screen.getByText('Shopping'));
            });
            expect(mockSetCategory).toHaveBeenCalledWith('Shopping');

            expect(mockSetCategory).toHaveBeenCalledTimes(2);
        });

        it('handles all available categories', async () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            // Wait for categories to load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/categories');
            });

            const trigger = screen.getByRole('combobox');

            const categories = ['Alcohol', 'Dining', 'Entertainment'];

            for (const category of categories) {
                await userEvent.click(trigger);
                await waitFor(async () => {
                    await userEvent.click(screen.getByText(category));
                });
                expect(mockSetCategory).toHaveBeenCalledWith(category);
            }
        });
    });

    describe('Accessibility', () => {
        it('has proper form control role', () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            const select = screen.getByRole('combobox');
            expect(select).toBeInTheDocument();
        });

        it('has proper label text', () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            expect(screen.getByText('Category')).toBeInTheDocument();
        });
    });

    describe('Loading and Error States', () => {
        it('shows loading placeholder when categories are loading', async () => {
            // Make the API return a pending promise (never resolves)
            (mockAxiosInstance.get as jest.Mock).mockImplementation((url: string) => {
                if (url === 'api/categories') {
                    return new Promise(() => {}); // Never resolves
                }
                return Promise.reject(new Error('Not found'));
            });

            render(
                <CategoryFilter
                    category=""
                    setCategory={mockSetCategory}
                />
            );

            // Should show loading placeholder
            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('Loading...');
            });
        });

        it('shows error placeholder when categories fail to load', async () => {
            // Make the API reject
            (mockAxiosInstance.get as jest.Mock).mockImplementation((url: string) => {
                if (url === 'api/categories') {
                    return Promise.reject(new Error('Failed to fetch'));
                }
                return Promise.reject(new Error('Not found'));
            });

            render(
                <CategoryFilter
                    category=""
                    setCategory={mockSetCategory}
                />
            );

            // Should show error placeholder
            await waitFor(() => {
                const trigger = screen.getByRole('combobox');
                expect(trigger).toHaveTextContent('Error loading categories');
            });
        });

        it('still shows "All" option even when categories fail to load', async () => {
            // Make the API reject
            (mockAxiosInstance.get as jest.Mock).mockImplementation((url: string) => {
                if (url === 'api/categories') {
                    return Promise.reject(new Error('Failed to fetch'));
                }
                return Promise.reject(new Error('Not found'));
            });

            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            // Wait for error state
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/categories');
            });

            // "All" should still be visible
            expect(screen.getByText('All')).toBeInTheDocument();
        });
    });

    describe('Component Structure', () => {
        it('renders all predefined categories', async () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            // Wait for categories to load
            await waitFor(() => {
                expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/categories');
            });

            // "All" is visible in the trigger
            expect(screen.getByText('All')).toBeInTheDocument();

            // Open the select to see other options
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const expectedCategories = ['Alcohol', 'Dining', 'Entertainment', 'Groceries', 'Hobbies', 'Income', 'Investment', 'Medical', 'Rent', 'Shopping', 'Subscription', 'Transfer', 'Transit', 'Travel'];

            await waitFor(() => {
                expectedCategories.forEach(category => {
                    expect(screen.getAllByText(category).length).toBeGreaterThanOrEqual(1);
                });
            });
        });
    });
});
