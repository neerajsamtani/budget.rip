import userEvent from '@testing-library/user-event';
import React, { useState } from 'react';
import { fireEvent, render, screen } from '../../utils/test-utils';
import YearFilter from '../YearFilter';

function YearFilterControlledWrapper({ initialValue = '2024' }: { initialValue?: string }) {
    const [value, setValue] = useState(initialValue);
    return <YearFilter year={value as any} setYear={setValue as any} />;
}

describe('YearFilter', () => {
    let rerender: any;

    function setup(initialValue = '2024') {
        const utils = render(<YearFilter year={initialValue as any} setYear={jest.fn()} />);
        rerender = utils.rerender;
        return utils;
    }

    describe('Rendering', () => {
        it('renders year filter component', () => {
            setup();
            expect(screen.getByText('Year')).toBeInTheDocument();
            expect(screen.getByRole('combobox')).toBeInTheDocument();
        });

        it('renders with proper form structure', () => {
            const { container } = setup();
            expect(container.querySelector('.input-group')).toBeInTheDocument();
            expect(container.querySelector('.input-group-text')).toBeInTheDocument();
            expect(container.querySelector('.form-select')).toBeInTheDocument();
        });

        it('displays current year value', () => {
            setup('2023');
            expect(screen.getByDisplayValue('2023')).toBeInTheDocument();
        });

        it('renders all year options', () => {
            setup();
            const options = ['2022', '2023', '2024', '2025'];
            options.forEach(option => {
                expect(screen.getByRole('option', { name: option })).toBeInTheDocument();
            });
        });
    });

    describe('User Interactions', () => {
        it('calls setYear when user selects different year', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, '2023');
            expect(screen.getByDisplayValue('2023')).toBeInTheDocument();
        });

        it('handles selection of all available years', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const select = screen.getByRole('combobox');
            const years = ['2022', '2023', '2024', '2025'];

            for (const year of years) {
                await userEvent.selectOptions(select, year);
                expect(screen.getByDisplayValue(year)).toBeInTheDocument();
            }
        });

        it('updates display value when year prop changes', () => {
            setup('2024');
            expect(screen.getByDisplayValue('2024')).toBeInTheDocument();
            rerender(<YearFilter year={'2023' as any} setYear={jest.fn()} />);
            expect(screen.getByDisplayValue('2023')).toBeInTheDocument();
        });

        it('maintains selection after user interaction', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, '2025');
            expect(select).toHaveValue('2025');
        });
    });

    describe('Props Handling', () => {
        it('accepts different initial year values', () => {
            setup('2022');
            expect(screen.getByDisplayValue('2022')).toBeInTheDocument();
        });

        it('handles all valid year values', () => {
            const years = ['2022', '2023', '2024', '2025'];
            years.forEach(year => {
                setup(year);
                expect(screen.getByDisplayValue(year)).toBeInTheDocument();
            });
        });

        it('defaults to 2024 when no initial value provided', () => {
            setup();
            expect(screen.getByDisplayValue('2024')).toBeInTheDocument();
        });
    });

    describe('Form Structure', () => {
        it('has proper input group structure', () => {
            const { container } = setup();
            expect(container.querySelector('.input-group')).toBeInTheDocument();
            expect(container.querySelector('.input-group-text')).toBeInTheDocument();
        });

        it('has proper select element', () => {
            const { container } = setup();
            const select = container.querySelector('.form-select');
            expect(select).toBeInTheDocument();
            expect(select).toHaveValue('2024');
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

        it('has proper option elements', () => {
            setup();
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(4);
            expect(options[0]).toHaveValue('2022');
            expect(options[1]).toHaveValue('2023');
            expect(options[2]).toHaveValue('2024');
            expect(options[3]).toHaveValue('2025');
        });

        it('maintains focus during selection', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const select = screen.getByRole('combobox');
            await userEvent.click(select);
            await userEvent.selectOptions(select, '2023');
            expect(select).toHaveFocus();
        });
    });

    describe('Edge Cases', () => {
        it('handles rapid year changes', async () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const select = screen.getByRole('combobox');

            await userEvent.selectOptions(select, '2022');
            await userEvent.selectOptions(select, '2025');
            await userEvent.selectOptions(select, '2023');

            expect(screen.getByDisplayValue('2023')).toBeInTheDocument();
        });

        it('maintains state after prop updates', () => {
            setup('2024');
            expect(screen.getByDisplayValue('2024')).toBeInTheDocument();
            rerender(<YearFilter year={'2022' as any} setYear={jest.fn()} />);
            expect(screen.getByDisplayValue('2022')).toBeInTheDocument();
        });

        it('handles fireEvent change directly', () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const select = screen.getByRole('combobox');
            fireEvent.change(select, { target: { value: '2025' } });
            expect(screen.getByDisplayValue('2025')).toBeInTheDocument();
        });
    });

    describe('State Management', () => {
        it('initializes with provided year value', () => {
            setup('2023');
            expect(screen.getByDisplayValue('2023')).toBeInTheDocument();
        });

        it('updates display when year changes', () => {
            setup('2022');
            expect(screen.getByDisplayValue('2022')).toBeInTheDocument();
            rerender(<YearFilter year={'2025' as any} setYear={jest.fn()} />);
            expect(screen.getByDisplayValue('2025')).toBeInTheDocument();
        });

        it('preserves selection during prop updates', () => {
            render(<YearFilterControlledWrapper initialValue="2024" />);
            const select = screen.getByRole('combobox');
            fireEvent.change(select, { target: { value: '2023' } });
            render(<YearFilterControlledWrapper initialValue="2025" />);
            expect(screen.getByDisplayValue('2025')).toBeInTheDocument();
        });
    });

    describe('Year Options', () => {
        it('renders exactly 4 year options', () => {
            setup();
            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(4);
        });

        it('renders years in correct order', () => {
            setup();
            const options = screen.getAllByRole('option');
            expect(options[0]).toHaveTextContent('2022');
            expect(options[1]).toHaveTextContent('2023');
            expect(options[2]).toHaveTextContent('2024');
            expect(options[3]).toHaveTextContent('2025');
        });

        it('has correct values for all options', () => {
            setup();
            const options = screen.getAllByRole('option');
            expect(options[0]).toHaveValue('2022');
            expect(options[1]).toHaveValue('2023');
            expect(options[2]).toHaveValue('2024');
            expect(options[3]).toHaveValue('2025');
        });
    });

    describe('Event Handling', () => {
        it('calls setYear with correct value on change', async () => {
            const mockSetYear = jest.fn();
            render(<YearFilter year={'2024' as any} setYear={mockSetYear} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, '2023');

            expect(mockSetYear).toHaveBeenCalledWith('2023');
        });

        it('handles multiple consecutive changes', async () => {
            const mockSetYear = jest.fn();
            render(<YearFilter year={'2024' as any} setYear={mockSetYear} />);

            const select = screen.getByRole('combobox');
            await userEvent.selectOptions(select, '2022');
            await userEvent.selectOptions(select, '2025');

            expect(mockSetYear).toHaveBeenCalledWith('2022');
            expect(mockSetYear).toHaveBeenCalledWith('2025');
        });
    });
}); 