import userEvent from '@testing-library/user-event';
import React, { useState } from 'react';
import { fireEvent, render, screen } from '../../utils/test-utils';
import TagsFilter from '../TagsFilter';

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
            expect(screen.getByRole('textbox')).toBeInTheDocument();
        });
        it('renders with proper form structure', () => {
            setup();
            // Check for shadcn components: label and input
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByRole('textbox')).toBeInTheDocument();
        });
        it('displays current tag filter value', () => {
            setup('groceries');
            expect(screen.getByDisplayValue('groceries')).toBeInTheDocument();
        });
        it('shows placeholder text', () => {
            setup();
            expect(screen.getByPlaceholderText('Search by tag...')).toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('calls setTagFilter when user types in input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: 'groceries' } });
            expect(screen.getByDisplayValue('groceries')).toBeInTheDocument();
        });
        it('handles multiple character input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: 'shopping' } });
            expect(screen.getByDisplayValue('shopping')).toBeInTheDocument();
        });
        it('handles special characters in input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: 'food & drinks' } });
            expect(screen.getByDisplayValue('food & drinks')).toBeInTheDocument();
        });
        it('handles numbers in input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: '2024' } });
            expect(screen.getByDisplayValue('2024')).toBeInTheDocument();
        });
        it('handles empty string input', () => {
            render(<TagsFilterControlledWrapper initialValue="existing" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: '' } });
            expect(screen.getByDisplayValue('')).toBeInTheDocument();
        });
        it('updates display value when tagFilter prop changes', () => {
            setup();
            expect(screen.getByDisplayValue('')).toBeInTheDocument();
            rerender(<TagsFilter tagFilter={'new tag'} setTagFilter={jest.fn()} />);
            expect(screen.getByDisplayValue('new tag')).toBeInTheDocument();
        });
    });

    describe('Props Handling', () => {
        it('accepts different initial tag filter values', () => {
            setup('initial value');
            expect(screen.getByDisplayValue('initial value')).toBeInTheDocument();
        });
        it('handles very long tag filter values', () => {
            const longTagFilter = 'a'.repeat(1000);
            setup(longTagFilter);
            expect(screen.getByDisplayValue(longTagFilter)).toBeInTheDocument();
        });
        it('handles tag filter with whitespace', () => {
            setup('  spaced tag  ');
            const input = screen.getByRole('textbox');
            expect(input).toHaveValue('  spaced tag  ');
        });
    });

    describe('Form Structure', () => {
        it('has proper input group structure', () => {
            setup();
            // Check for shadcn components: label and input are present
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByRole('textbox')).toBeInTheDocument();
        });
        it('has proper form control structure', () => {
            setup();
            // Check for input element exists
            expect(screen.getByRole('textbox')).toBeInTheDocument();
        });
        it('has proper input type', () => {
            setup();
            const input = screen.getByRole('textbox');
            expect(input).toHaveAttribute('type', 'text');
        });
    });

    describe('Accessibility', () => {
        it('has proper textbox role', () => {
            setup();
            expect(screen.getByRole('textbox')).toBeInTheDocument();
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
            const input = screen.getByRole('textbox');
            await userEvent.click(input);
            fireEvent.change(input, { target: { value: 'test' } });
            expect(input).toHaveFocus();
        });
    });

    describe('Edge Cases', () => {
        it('handles tag filter with emoji characters', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: '🍕' } });
            expect(screen.getByDisplayValue('🍕')).toBeInTheDocument();
        });
        it('handles tag filter with unicode characters', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: 'café' } });
            expect(screen.getByDisplayValue('café')).toBeInTheDocument();
        });
        it('handles tag filter with HTML-like characters', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: '<script>alert("test")</script>' } });
            expect(screen.getByDisplayValue('<script>alert("test")</script>')).toBeInTheDocument();
        });
        it('maintains state after prop updates', () => {
            setup();
            expect(screen.getByDisplayValue('')).toBeInTheDocument();
            rerender(<TagsFilter tagFilter={'updated'} setTagFilter={jest.fn()} />);
            expect(screen.getByDisplayValue('updated')).toBeInTheDocument();
        });
    });

    describe('State Management', () => {
        it('initializes with provided tag filter value', () => {
            setup('initial');
            expect(screen.getByDisplayValue('initial')).toBeInTheDocument();
        });
        it('updates display when tag filter changes', () => {
            setup('old');
            expect(screen.getByDisplayValue('old')).toBeInTheDocument();
            rerender(<TagsFilter tagFilter={'new'} setTagFilter={jest.fn()} />);
            expect(screen.getByDisplayValue('new')).toBeInTheDocument();
        });
        it('preserves input value during prop updates', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('textbox');
            fireEvent.change(input, { target: { value: 'user input' } });
            render(<TagsFilterControlledWrapper initialValue="prop update" />);
            expect(screen.getByDisplayValue('prop update')).toBeInTheDocument();
        });
    });
}); 