import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen } from '../../utils/test-utils';
import CategoryFilter from '../CategoryFilter';
import { Category } from '@/constants/categories';

describe('CategoryFilter', () => {
    const mockSetCategory = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
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

            // Open select to see all options
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            expect(screen.getAllByText('Entertainment').length).toBeGreaterThanOrEqual(1);
            expect(screen.getAllByText('Shopping').length).toBeGreaterThanOrEqual(1);
            expect(screen.getAllByText('Travel').length).toBeGreaterThanOrEqual(1);
        });

        it('shows selected category when provided', () => {
            render(
                <CategoryFilter
                    category="Entertainment"
                    setCategory={mockSetCategory}
                />
            );

            expect(screen.getByText('Entertainment')).toBeInTheDocument();
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

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const entertainmentOption = screen.getByText('Entertainment');
            await userEvent.click(entertainmentOption);

            expect(mockSetCategory).toHaveBeenCalledWith('Entertainment');
        });

        it('calls setCategory with "All" when All is selected', async () => {
            render(
                <CategoryFilter
                    category="Entertainment"
                    setCategory={mockSetCategory}
                />
            );

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Find the "All" option in the dropdown
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

            const trigger = screen.getByRole('combobox');

            // First selection
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('Entertainment'));
            expect(mockSetCategory).toHaveBeenCalledWith('Entertainment');

            // Second selection
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('Shopping'));
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

            const trigger = screen.getByRole('combobox');

            const categories: Category[] = ['Alcohol', 'Dining', 'Entertainment'];

            for (const category of categories) {
                await userEvent.click(trigger);
                await userEvent.click(screen.getByText(category));
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
        it('renders all predefined categories', async () => {
            render(
                <CategoryFilter
                    category="All"
                    setCategory={mockSetCategory}
                />
            );

            // "All" is visible in the trigger
            expect(screen.getByText('All')).toBeInTheDocument();

            // Open the select to see other options
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const expectedCategories = ['Alcohol', 'Dining', 'Entertainment', 'Forma', 'Groceries', 'Hobbies', 'Income', 'Investment', 'Medical', 'Rent', 'Shopping', 'Subscription', 'Transfer', 'Transit', 'Travel'];

            expectedCategories.forEach(category => {
                expect(screen.getAllByText(category).length).toBeGreaterThanOrEqual(1);
            });
        });
    });
}); 