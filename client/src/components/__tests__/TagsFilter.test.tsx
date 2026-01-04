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
        it('tags filter component is displayed', () => {
            setup();
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('proper form structure is rendered', () => {
            setup();
            // Check for shadcn components: label and input
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('current tag filter value is displayed when tag exists in options', () => {
            jest.spyOn(require('@/hooks/useApi'), 'useTags').mockReturnValue({
                data: [{ id: 'tag_1', name: 'groceries' }],
                isLoading: false,
                isError: false
            });

            setup('groceries');
            const input = screen.getByRole('combobox');
            expect(input).toHaveValue('groceries');
        });
        it('placeholder text is shown', () => {
            setup();
            expect(screen.getByPlaceholderText('Search by tag...')).toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('setTagFilter is called when user types in input', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: 'groceries' } });
            expect(screen.getByDisplayValue('groceries')).toBeInTheDocument();
        });
        it('multiple character input is handled', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: 'shopping' } });
            expect(screen.getByDisplayValue('shopping')).toBeInTheDocument();
        });
        it('special characters in input are handled', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: 'food & drinks' } });
            expect(screen.getByDisplayValue('food & drinks')).toBeInTheDocument();
        });
        it('numbers in input are handled', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: '2024' } });
            expect(screen.getByDisplayValue('2024')).toBeInTheDocument();
        });
        it('empty string input is handled', () => {
            render(<TagsFilterControlledWrapper initialValue="existing" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: '' } });
            expect(screen.getByDisplayValue('')).toBeInTheDocument();
        });
    });


    describe('Form Structure', () => {
        it('proper input group structure is present', () => {
            setup();
            // Check for shadcn components: label and input are present
            expect(screen.getByText('Tags')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('proper form control structure is present', () => {
            setup();
            // Check for input element exists
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('proper input type is set', () => {
            setup();
            const input = screen.getByRole('combobox');
            expect(input).toHaveAttribute('type', 'text');
        });
    });

    describe('Accessibility', () => {
        it('proper textbox role is set', () => {
            setup();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });
        it('proper label text is displayed', () => {
            setup();
            expect(screen.getByText('Tags')).toBeInTheDocument();
        });
        it('proper placeholder text is set', () => {
            setup();
            expect(screen.getByPlaceholderText('Search by tag...')).toBeInTheDocument();
        });
        it('focus is maintained during typing', async () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            await userEvent.click(input);
            fireEvent.change(input, { target: { value: 'test' } });
            expect(input).toHaveFocus();
        });
    });

    describe('Edge Cases', () => {
        it('emoji characters in tag filter are handled', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: '🍕' } });
            expect(screen.getByDisplayValue('🍕')).toBeInTheDocument();
        });
        it('unicode characters in tag filter are handled', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: 'café' } });
            expect(screen.getByDisplayValue('café')).toBeInTheDocument();
        });
        it('HTML-like characters in tag filter are handled', () => {
            render(<TagsFilterControlledWrapper initialValue="" />);
            const input = screen.getByRole('combobox');
            fireEvent.change(input, { target: { value: '<script>alert("test")</script>' } });
            expect(screen.getByDisplayValue('<script>alert("test")</script>')).toBeInTheDocument();
        });
    });

}); 