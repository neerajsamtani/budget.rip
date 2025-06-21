import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen } from '../../utils/test-utils';
import CategoryFilter, { Category } from '../CategoryFilter';

describe('CategoryFilter', () => {
    const mockSetCategory = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Rendering', () => {
        it('renders category filter with all categories', () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            expect(screen.getByText('Category')).toBeInTheDocument();
            expect(screen.getByText('All')).toBeInTheDocument();
            expect(screen.getByText('Entertainment')).toBeInTheDocument();
            expect(screen.getByText('Shopping')).toBeInTheDocument();
            expect(screen.getByText('Travel')).toBeInTheDocument();
        });

        it('shows selected category when provided', () => {
            render(
                <CategoryFilter
                    category="Entertainment"
                    setCategory={mockSetCategory}
                />
            );

            const select = screen.getByRole('combobox') as HTMLSelectElement;
            expect(select.value).toBe('Entertainment');
        });

        it('shows "All" when All category is selected', () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            const select = screen.getByRole('combobox') as HTMLSelectElement;
            expect(select.value).toBe('All');
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

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'Entertainment');

            expect(mockSetCategory).toHaveBeenCalledWith('Entertainment');
        });

        it('calls setCategory with "All" when All is selected', async () => {
            render(
                <CategoryFilter
                    category="Entertainment"
                    setCategory={mockSetCategory}
                />
            );

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, 'All');

            expect(mockSetCategory).toHaveBeenCalledWith('All');
        });

        it('handles multiple category selections', async () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            const select = screen.getByRole('combobox');

            await userEvent.selectOptions(select, 'Entertainment');
            expect(mockSetCategory).toHaveBeenCalledWith('Entertainment');

            await userEvent.selectOptions(select, 'Shopping');
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

            const select = screen.getByRole('combobox');

            const categories: Category[] = ['Alcohol', 'Dining', 'Entertainment', 'Forma', 'Groceries', 'Hobbies', 'Income', 'Investment', 'Medical', 'Rent', 'Shopping', 'Subscription', 'Transfer', 'Transit', 'Travel'];

            for (const category of categories) {
                await userEvent.selectOptions(select, category);
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

    describe('Component Structure', () => {
        it('renders all predefined categories', () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            const expectedCategories = ['All', 'Alcohol', 'Dining', 'Entertainment', 'Forma', 'Groceries', 'Hobbies', 'Income', 'Investment', 'Medical', 'Rent', 'Shopping', 'Subscription', 'Transfer', 'Transit', 'Travel'];

            expectedCategories.forEach(category => {
                expect(screen.getByText(category)).toBeInTheDocument();
            });
        });
    });
}); 