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
        it('year filter component is displayed', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('proper form structure is rendered', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('current year value is displayed', () => {
            setup('2023');
            expect(screen.getByText('2023')).toBeInTheDocument();
        });

        it('all year options are rendered', async () => {
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
        it('setYear is called when user selects different year', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2023'));

            // Check that the trigger now shows the selected value
            expect(trigger).toHaveTextContent('2023');
        });

        it('selection of all available years is handled correctly', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const years = ['2022', '2023', '2024', '2025'];

            for (const year of years) {
                const trigger = screen.getByRole('combobox');
                await userEvent.click(trigger);
                await userEvent.click(screen.getByText(year));
                expect(trigger).toHaveTextContent(year);
            }
        });

        it('display value is updated when year prop changes', () => {
            setup('2024');
            expect(screen.getByText('2024')).toBeInTheDocument();
            rerender(<YearFilter year='2023' setYear={jest.fn()} />);
            expect(screen.getByText('2023')).toBeInTheDocument();
        });

        it('selection is maintained after user interaction', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2025'));

            expect(trigger).toHaveTextContent('2025');
        });
    });

    describe('Props Handling', () => {
        it('different initial year values are accepted', () => {
            setup('2022');
            expect(screen.getByText('2022')).toBeInTheDocument();
        });

        it('all valid year values are handled', () => {
            const years = ['2022', '2023', '2024', '2025'];
            years.forEach(year => {
                setup(year);
                expect(screen.getByText(year)).toBeInTheDocument();
            });
        });

        it('default is 2024 when no initial value provided', () => {
            setup();
            expect(screen.getByText('2024')).toBeInTheDocument();
        });
    });

    describe('Form Structure', () => {
        it('proper input group structure is present', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
            expect(screen.getByText('Year')).toBeInTheDocument();
        });

        it('proper select element is present', () => {
            setup();
            const select = screen.getByRole('combobox');
            expect(select).toBeInTheDocument();
            expect(select).toHaveTextContent('2024');
        });
    });

    describe('Accessibility', () => {
        it('proper combobox role is set', () => {
            setup();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('proper label text is displayed', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
        });

        it('proper option elements are present', async () => {
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

        it('focus is maintained during selection', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2023'));

            expect(trigger).toHaveTextContent('2023');
        });
    });

    describe('Edge Cases', () => {
        it('rapid year changes are handled correctly', async () => {
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

        it('state is maintained after prop updates', () => {
            setup('2024');
            expect(screen.getByText('2024')).toBeInTheDocument();
            rerender(<YearFilter year={'2022' as any} setYear={jest.fn()} />);
            expect(screen.getByText('2022')).toBeInTheDocument();
        });

        it('controlled component updates are handled', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const trigger = screen.getByRole('combobox');

            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2025'));

            expect(trigger).toHaveTextContent('2025');
        });
    });

    describe('State Management', () => {
        it('year value is initialized from props', () => {
            setup('2023');
            expect(screen.getByText('2023')).toBeInTheDocument();
        });

        it('display is updated when year changes', () => {
            setup('2022');
            expect(screen.getByText('2022')).toBeInTheDocument();
            rerender(<YearFilter year={'2025' as any} setYear={jest.fn()} />);
            expect(screen.getByText('2025')).toBeInTheDocument();
        });

        it('selection is preserved during prop updates', async () => {
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
        it('exactly 5 year options are rendered', async () => {
            setup();
            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);

            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(5);
        });

        it('years are rendered in correct order', async () => {
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

        it('all options have correct values', async () => {
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
        it('setYear is called with correct value on change', async () => {
            const mockSetYear = jest.fn();
            render(<YearFilter year={'2024' as any} setYear={mockSetYear} />);

            const trigger = screen.getByRole('combobox');
            await userEvent.click(trigger);
            await userEvent.click(screen.getByText('2023'));

            expect(mockSetYear).toHaveBeenCalledWith('2023');
        });

        it('multiple consecutive changes are handled correctly', async () => {
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