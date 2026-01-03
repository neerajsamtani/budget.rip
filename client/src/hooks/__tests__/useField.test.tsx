import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { render, screen } from '../../utils/test-utils';
import { useField } from '../useField';

// Test component to use the hook
const TestComponent = ({ type, defaultValue }: { type: string; defaultValue: string }) => {
    const field = useField(type, defaultValue);

    return (
        <div>
            <input
                type={field.type}
                value={field.value}
                onChange={field.onChange}
                data-testid="test-input"
            />
            <button onClick={field.setEmpty} data-testid="set-empty">Set Empty</button>
            <button onClick={() => field.setCustomValue('custom')} data-testid="set-custom">Set Custom</button>
            <span data-testid="value-display">{field.value}</span>
        </div>
    );
};

describe('useField', () => {
    describe('Initialization', () => {
        it('field initializes with provided default value', () => {
            render(<TestComponent type="text" defaultValue="initial value" />);

            expect(screen.getByTestId('value-display')).toHaveTextContent('initial value');
            expect(screen.getByTestId('test-input')).toHaveAttribute('type', 'text');
        });

        it('field initializes with empty string when no default is provided', () => {
            render(<TestComponent type="text" defaultValue="" />);

            expect(screen.getByTestId('value-display')).toHaveTextContent('');
            expect(screen.getByTestId('test-input')).toHaveAttribute('type', 'text');
        });

        it('field supports different input types', () => {
            const { rerender } = render(<TestComponent type="text" defaultValue="text value" />);
            expect(screen.getByTestId('test-input')).toHaveAttribute('type', 'text');

            rerender(<TestComponent type="password" defaultValue="password value" />);
            expect(screen.getByTestId('test-input')).toHaveAttribute('type', 'password');

            rerender(<TestComponent type="email" defaultValue="email value" />);
            expect(screen.getByTestId('test-input')).toHaveAttribute('type', 'email');
        });
    });

    describe('onChange functionality', () => {
        it('value is updated when user types', async () => {
            render(<TestComponent type="text" defaultValue="" />);

            const input = screen.getByTestId('test-input');
            fireEvent.change(input, { target: { value: 'new value' } });

            expect(screen.getByTestId('value-display')).toHaveTextContent('new value');
        });

        it('empty string is handled in onChange', async () => {
            render(<TestComponent type="text" defaultValue="initial" />);

            const input = screen.getByTestId('test-input');
            await userEvent.clear(input);

            expect(screen.getByTestId('value-display')).toHaveTextContent('');
        });

        it('special characters are handled in onChange', async () => {
            render(<TestComponent type="text" defaultValue="" />);

            const input = screen.getByTestId('test-input');
            fireEvent.change(input, { target: { value: 'test@example.com' } });

            expect(screen.getByTestId('value-display')).toHaveTextContent('test@example.com');
        });

        it('multiple character input is handled', async () => {
            render(<TestComponent type="text" defaultValue="" />);

            const input = screen.getByTestId('test-input');
            fireEvent.change(input, { target: { value: 'hello world' } });

            expect(screen.getByTestId('value-display')).toHaveTextContent('hello world');
        });

        it('value is replaced when typing after clearing', async () => {
            render(<TestComponent type="text" defaultValue="initial" />);

            const input = screen.getByTestId('test-input');
            await userEvent.clear(input);
            fireEvent.change(input, { target: { value: 'new value' } });

            expect(screen.getByTestId('value-display')).toHaveTextContent('new value');
        });
    });

    describe('setCustomValue functionality', () => {
        it('value is updated when setCustomValue is called', async () => {
            render(<TestComponent type="text" defaultValue="initial" />);

            const setCustomButton = screen.getByTestId('set-custom');
            await userEvent.click(setCustomButton);

            expect(screen.getByTestId('value-display')).toHaveTextContent('custom');
        });

        it('value updates correctly with multiple setCustomValue calls', async () => {
            render(<TestComponent type="text" defaultValue="initial" />);

            const setCustomButton = screen.getByTestId('set-custom');

            await userEvent.click(setCustomButton);
            expect(screen.getByTestId('value-display')).toHaveTextContent('custom');

            await userEvent.click(setCustomButton);
            expect(screen.getByTestId('value-display')).toHaveTextContent('custom');
        });
    });

    describe('setEmpty functionality', () => {
        it('value becomes empty string when setEmpty is called', async () => {
            render(<TestComponent type="text" defaultValue="initial value" />);

            const setEmptyButton = screen.getByTestId('set-empty');
            await userEvent.click(setEmptyButton);

            expect(screen.getByTestId('value-display')).toHaveTextContent('');
        });

        it('setEmpty can be called multiple times', async () => {
            render(<TestComponent type="text" defaultValue="initial value" />);

            const setEmptyButton = screen.getByTestId('set-empty');
            const setCustomButton = screen.getByTestId('set-custom');

            await userEvent.click(setCustomButton);
            expect(screen.getByTestId('value-display')).toHaveTextContent('custom');

            await userEvent.click(setEmptyButton);
            expect(screen.getByTestId('value-display')).toHaveTextContent('');

            await userEvent.click(setCustomButton);
            expect(screen.getByTestId('value-display')).toHaveTextContent('custom');

            await userEvent.click(setEmptyButton);
            expect(screen.getByTestId('value-display')).toHaveTextContent('');
        });
    });

    describe('Integration scenarios', () => {
        it('typical form field usage pattern works correctly', async () => {
            render(<TestComponent type="text" defaultValue="" />);

            const input = screen.getByTestId('test-input');
            const setEmptyButton = screen.getByTestId('set-empty');

            // Initial state
            expect(screen.getByTestId('value-display')).toHaveTextContent('');

            // User types
            fireEvent.change(input, { target: { value: 'h' } });
            expect(screen.getByTestId('value-display')).toHaveTextContent('h');

            // User continues typing
            fireEvent.change(input, { target: { value: 'hello' } });
            expect(screen.getByTestId('value-display')).toHaveTextContent('hello');

            // Form is reset
            await userEvent.click(setEmptyButton);
            expect(screen.getByTestId('value-display')).toHaveTextContent('');
        });

        it('form field with initial value handles user interaction correctly', async () => {
            render(<TestComponent type="email" defaultValue="user@example.com" />);

            const input = screen.getByTestId('test-input');

            expect(screen.getByTestId('value-display')).toHaveTextContent('user@example.com');
            expect(input).toHaveAttribute('type', 'email');

            await userEvent.clear(input);
            fireEvent.change(input, { target: { value: 'new@example.com' } });

            expect(screen.getByTestId('value-display')).toHaveTextContent('new@example.com');
        });
    });
}); 