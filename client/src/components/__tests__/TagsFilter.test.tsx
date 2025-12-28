import userEvent from '@testing-library/user-event';
import React, { useState } from 'react';
import { fireEvent, render, screen } from '../../utils/test-utils';
import TagsFilter from '../TagsFilter';

// Mock the useApi hook
jest.mock('@/hooks/useApi', () => ({
    ...jest.requireActual('@/hooks/useApi'),
    useTags: jest.fn(() => ({
        data: [],
        isLoading: false,
        isError: false,
    })),
}));

function TagsFilterControlledWrapper({ initialValue = '' }: { initialValue?: string }) {
    const [value, setValue] = useState(initialValue);
    return <TagsFilter tagFilter={value} setTagFilter={setValue} />;
}

describe('TagsFilter', () => {
    let rerender: (_ui: React.ReactElement) => void;

    function setup(initialValue = '') {
        const { rerender: setRerender } = render(<TagsFilter tagFilter={initialValue} setTagFilter={jest.fn()} />);
        rerender = setRerender;
    }

    describe('Rendering', () => {
        it('renders tags filter component', () => {
            setup();
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('renders with proper form structure', () => {
            setup();
            // Check for shadcn components: label and input
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('displays current tag filter value when tag exists in options', () => {
            jest.spyOn(require('@/hooks/useApi'), 'useTags').mockReturnValue({
                data: [{ id: 'tag_1', name: 'groceries' }],
                isLoading: false,
                isError: false
            });

            setup('groceries');
            const input = screen.getByRole('combobox');
            expect(input).toHaveValue('groceries');
        });
        it('shows placeholder text', () => {
            setup();
            expect(screen.getByPlaceholderText('Search by tag...')).toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('calls setTagFilter when user types in input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: 'groceries' } });
            expect(screen.getByDisplayValue('groceries')).toBeInTheDocument();
        });
        it('handles multiple character input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: 'shopping' } });
            expect(screen.getByDisplayValue('shopping')).toBeInTheDocument();
        });
        it('handles special characters in input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: 'food & drinks' } });
            expect(screen.getByDisplayValue('food & drinks')).toBeInTheDocument();
        });
        it('handles numbers in input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: '2024' } });
            expect(screen.getByDisplayValue('2024')).toBeInTheDocument();
        });
        it('handles empty string input', () => {
            render(<TagsFilterControlledWrapper initialValue="existing" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: '' } });
            expect(screen.getByDisplayValue('')).toBeInTheDocument();
        });
    });


    describe('Form Structure', () => {
        it('has proper input group structure', () => {
            setup();
            // Check for shadcn components: label and input are present
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('has proper form control structure', () => {
            setup();
            // Check for input element exists
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('has proper input type', () => {
            setup();
            const input = screen.getByRole('combobox');
            expect(input).toHaveAttribute('type', 'text');
        });
    });

    describe('Accessibility', () => {
        it('has proper textbox role', () => {
            setup();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('has proper label text', () => {
            setup();
            expect(screen.getByText('Tags')).toBeInTheDocument();
        });
        it('has proper placeholder text', () => {
            setup();
            expect(screen.getByPlaceholderText('Search by tag...')).toBeInTheDocument();
        });
        it('maintains focus during typing', async () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            await userEvent.click(input);
            fireEvent.change(input, { target: { value: 'test' } });
            expect(input).toHaveFocus();
        });
    });

    describe('Edge Cases', () => {
        it('handles tag filter with emoji characters', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: '🍕' } });
            expect(screen.getByDisplayValue('🍕')).toBeInTheDocument();
        });
        it('handles tag filter with unicode characters', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: 'café' } });
            expect(screen.getByDisplayValue('café')).toBeInTheDocument();
        });
        it('handles tag filter with HTML-like characters', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: '<script>alert("test")</script>' } });
            expect(screen.getByDisplayValue('<script>alert("test")</script>')).toBeInTheDocument();
        });
    });

}); 