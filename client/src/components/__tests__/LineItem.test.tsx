import React from 'react';
import { mockLineItem, render, screen } from '../../utils/test-utils';
import LineItem from '../LineItem';

// Mock the context hook
jest.mock('../../contexts/LineItemsContext', () => ({
    useLineItems: jest.fn(() => []),
    useLineItemsDispatch: jest.fn(() => jest.fn()),
}));

describe('LineItem', () => {
    it('renders line item data correctly', () => {
        render(
            <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
        );

        expect(screen.getByText('Test transaction')).toBeInTheDocument();
        expect(screen.getByText('Test Store')).toBeInTheDocument();
        expect(screen.getByText('credit_card')).toBeInTheDocument();
        expect(screen.getByText('50')).toBeInTheDocument();
    });

    it('renders checkbox when showCheckBox is true', () => {
        render(
            <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={true} /></tbody></table>
        );

        const checkbox = screen.getByRole('checkbox');
        expect(checkbox).toBeInTheDocument();
    });

    it('does not render checkbox when showCheckBox is false', () => {
        render(
            <table><tbody><LineItem lineItem={mockLineItem} showCheckBox={false} /></tbody></table>
        );

        const checkbox = screen.queryByRole('checkbox');
        expect(checkbox).not.toBeInTheDocument();
    });

    it('does not render checkbox when showCheckBox is not provided', () => {
        render(
            <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
        );

        const checkbox = screen.queryByRole('checkbox');
        expect(checkbox).not.toBeInTheDocument();
    });

    it('formats date correctly', () => {
        render(
            <table><tbody><LineItem lineItem={mockLineItem} /></tbody></table>
        );

        // The mock date is 1640995200 which should format to Jan 1, 2022
        expect(screen.getByText('Jan 1, 2022')).toBeInTheDocument();
    });
}); 