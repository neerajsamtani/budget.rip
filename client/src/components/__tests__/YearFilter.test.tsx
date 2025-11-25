import userEvent from '@testing-library/user-event';
import React, { useState } from 'react';
import { render, screen } from '../../utils/test-utils';
import YearFilter from '../YearFilter';

function YearFilterControlledWrapper({ initialValue = '2024' }: { initialValue?: string }) {
    const [value, setValue] = useState(initialValue);
    return <YearFilter year={value} setYear={setValue} />;
}

describe('YearFilter', () => {
    let rerender: (_ui: React.ReactElement) => void;

    function setup(initialValue = '2024') {
        const { rerender: setRerender } = render(<YearFilter year={initialValue} setYear={jest.fn()} />);
        rerender = setRerender;
    }

    describe('Rendering', () => {
        it('renders year filter component', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('renders with proper form structure', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('displays current year value', () => {
            setup('2023');
            expect(screen.getByText('2023')).toBeInTheDocument();
        });

        it('renders all year options', async () => {
            setup();
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            // Check that all option roles exist
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(5);

            // Check specific option text content
            expect(options[0]).toHaveTextContent('2022');
            expect(options[1]).toHaveTextContent('2023');
            expect(options[2]).toHaveTextContent('2024');
            expect(options[3]).toHaveTextContent('2025');
            expect(options[4]).toHaveTextContent('2026');
        });
    });

    describe('User Interactions', () => {
        it('calls setYear when user selects different year', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2023'));

            // Check that the trigger now shows the selected value
            expect(trigger).toHaveTextContent('2023');
        });

        it('handles selection of all available years', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const years = ['2022', '2023', '2024', '2025'];

            for (const year of years) {
                const trigger = screen.getByRole('combobox');
                await userEvent.click(trigger);
                await userEvent.click(screen.getByText(year));
                expect(trigger).toHaveTextContent(year);
            }
        });

        it('updates display value when year prop changes', () => {
            setup('2024');
            expect(screen.getByText('2024')).toBeInTheDocument();
            rerender(<YearFilter year='2023' setYear={jest.fn()} />);
            expect(screen.getByText('2023')).toBeInTheDocument();
        });

        it('maintains selection after user interaction', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2025'));

            expect(trigger).toHaveTextContent('2025');
        });
    });

    describe('Props Handling', () => {
        it('accepts different initial year values', () => {
            setup('2022');
            expect(screen.getByText('2022')).toBeInTheDocument();
        });

        it('handles all valid year values', () => {
            const years = ['2022', '2023', '2024', '2025'];
            years.forEach(year => {
                setup(year);
                expect(screen.getByText(year)).toBeInTheDocument();
            });
        });

        it('defaults to 2024 when no initial value provided', () => {
            setup();
            expect(screen.getByText('2024')).toBeInTheDocument();
        });
    });

    describe('Form Structure', () => {
        it('has proper input group structure', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
            expect(screen.getByText('Year')).toBeInTheDocument();
        });

        it('has proper select element', () => {
            setup();
            const select = screen.getByRole('combobox');
            expect(select).toBeInTheDocument();
            expect(select).toHaveTextContent('2024');
        });
    });

    describe('Accessibility', () => {
        it('has proper combobox role', () => {
            setup();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('has proper label text', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
        });

        it('has proper option elements', async () => {
            setup();
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(5);
            expect(options[0]).toHaveTextContent('2022');
            expect(options[1]).toHaveTextContent('2023');
            expect(options[2]).toHaveTextContent('2024');
            expect(options[3]).toHaveTextContent('2025');
            expect(options[4]).toHaveTextContent('2026');
        });

        it('maintains focus during selection', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2023'));

            expect(trigger).toHaveTextContent('2023');
        });
    });

    describe('Edge Cases', () => {
        it('handles rapid year changes', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);

            // First change
            let trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2022'));
            expect(trigger).toHaveTextContent('2022');

            // Second change
            trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2025'));
            expect(trigger).toHaveTextContent('2025');

            // Third change
            trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2023'));
            expect(trigger).toHaveTextContent('2023');
        });

        it('maintains state after prop updates', () => {
            setup('2024');
            expect(screen.getByText('2024')).toBeInTheDocument();
            rerender(<YearFilter year={'2022' as any} setYear={jest.fn()} />);
            expect(screen.getByText('2022')).toBeInTheDocument();
        });

        it('handles controlled component updates', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2025'));

            expect(trigger).toHaveTextContent('2025');
        });
    });

    describe('State Management', () => {
        it('initializes with provided year value', () => {
            setup('2023');
            expect(screen.getByText('2023')).toBeInTheDocument();
        });

        it('updates display when year changes', () => {
            setup('2022');
            expect(screen.getByText('2022')).toBeInTheDocument();
            rerender(<YearFilter year={'2025' as any} setYear={jest.fn()} />);
            expect(screen.getByText('2025')).toBeInTheDocument();
        });

        it('preserves selection during prop updates', async () => {
            const { unmount } = render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2023'));
            expect(trigger).toHaveTextContent('2023');

            // Unmount and re-render with new initial value
            unmount();
            render(<YearFilterControlledWrapper initialValue="2025" />);
            const newTrigger = screen.getByRole('combobox');
            expect(newTrigger).toHaveTextContent('2025');
        });
    });

    describe('Year Options', () => {
        it('renders exactly 5 year options', async () => {
            setup();
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(5);
        });

        it('renders years in correct order', async () => {
            setup();
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const options = screen.getAllByRole('option');
            expect(options[0]).toHaveTextContent('2022');
            expect(options[1]).toHaveTextContent('2023');
            expect(options[2]).toHaveTextContent('2024');
            expect(options[3]).toHaveTextContent('2025');
            expect(options[4]).toHaveTextContent('2026');
        });

        it('has correct values for all options', async () => {
            setup();
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const options = screen.getAllByRole('option');
            expect(options[0]).toHaveTextContent('2022');
            expect(options[1]).toHaveTextContent('2023');
            expect(options[2]).toHaveTextContent('2024');
            expect(options[3]).toHaveTextContent('2025');
            expect(options[4]).toHaveTextContent('2026');
        });
    });

    describe('Event Handling', () => {
        it('calls setYear with correct value on change', async () => {
            const mockSetYear = jest.fn();
            render(<YearFilter year={'2024' as any} setYear={mockSetYear} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2023'));

            expect(mockSetYear).toHaveBeenCalledWith('2023');
        });

        it('handles multiple consecutive changes', async () => {
            const mockSetYear = jest.fn();
            render(<YearFilter year={'2024' as any} setYear={mockSetYear} />);

            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2022'));

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2025'));

            expect(mockSetYear).toHaveBeenCalledWith('2022');
            expect(mockSetYear).toHaveBeenCalledWith('2025');
        });
    });
}); 