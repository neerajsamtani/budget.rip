import { LineItemInterface } from '../../contexts/LineItemsContext';
import { getPrefillFromLineItems } from "../EventHints";

// Mock line item factory for consistent test data
const createMockLineItem = (overrides: Partial<LineItemInterface> = {}): LineItemInterface => ({
    _id: '1',
    id: '1',
    date: 1629984000,
    payment_method: 'credit_card',
    description: 'Test transaction',
    responsible_party: 'Test Store',
    amount: 50.00,
    isSelected: false,
    ...overrides,
});

describe('getPrefillFromLineItems', () => {
    describe('Basic Functionality', () => {
        it('returns null for empty array', () => {
            expect(getPrefillFromLineItems([])).toBeNull();
        });

        it('returns null for null input', () => {
            expect(getPrefillFromLineItems(null as any)).toBeNull();
        });

        it('returns null for undefined input', () => {
            expect(getPrefillFromLineItems(undefined as any)).toBeNull();
        });

        it('returns null when no hints match', () => {
            const lineItems = [
                createMockLineItem({
                    description: 'Random Purchase',
                    amount: 25.00,
                }),
            ];
            expect(getPrefillFromLineItems(lineItems)).toBeNull();
        });
    });

    describe('Subscription Hints', () => {
        it('matches Spotify subscription', () => {
            const lineItems = [
                createMockLineItem({
                    description: 'Spotify Premium Subscription',
                    amount: 9.99,
                }),
            ];
            expect(getPrefillFromLineItems(lineItems)).toEqual({
                name: 'Spotify',
                category: 'Subscription',
            });
        });

        it('matches AMC A-List subscription with exact amount', () => {
            const lineItems = [
                createMockLineItem({
                    description: 'AMC A-List Monthly Subscription',
                    amount: 23.95,
                }),
            ];
            expect(getPrefillFromLineItems(lineItems)).toEqual({
                name: 'AMC A-List',
                category: 'Subscription',
            });
        });

        it('does not match AMC without exact amount', () => {
            const lineItems = [
                createMockLineItem({
                    description: 'AMC A-List Monthly Subscription',
                    amount: 25.00,
                }),
            ];
            expect(getPrefillFromLineItems(lineItems)).toBeNull();
        });
    });

    describe('Edge Cases', () => {
        it('handles line items with missing properties gracefully', () => {
            const incompleteLineItem = {
                _id: '1',
                id: '1',
                date: 1629984000,
                // Missing other properties
            } as any;

            // The CEL evaluator will throw an error when trying to access undefined properties
            // This is the expected behavior for malformed data
            expect(() => getPrefillFromLineItems([incompleteLineItem])).toThrow(TypeError);
        });

        it('handles empty description', () => {
            const lineItems = [
                createMockLineItem({
                    description: '',
                    amount: 50.00,
                }),
            ];
            expect(getPrefillFromLineItems(lineItems)).toBeNull();
        });
    });
});

describe('getPrefillFromLineItems - parameterized', () => {
    const testCases = [
        {
            name: 'Spotify Subscription',
            lineItems: [
                {
                    _id: '1',
                    id: '1',
                    date: 1629984000,
                    payment_method: 'Credit Card',
                    description: 'Spotify Premium Subscription',
                    responsible_party: 'John Doe',
                    amount: 9.99,
                },
            ],
            expectedPrefill: { name: 'Spotify', category: 'Subscription' },
        },
        {
            name: 'AMC A-List Subscription',
            lineItems: [
                {
                    _id: '2',
                    id: '2',
                    date: 1630070400,
                    payment_method: 'Credit Card',
                    description: 'AMC A-List Monthly Subscription',
                    responsible_party: 'Jane Doe',
                    amount: 23.95,
                },
            ],
            expectedPrefill: { name: 'AMC A-List', category: 'Subscription' },
        },
        {
            name: 'No Match',
            lineItems: [
                {
                    _id: '4',
                    id: '4',
                    date: 1630243200,
                    payment_method: 'Credit Card',
                    description: 'Groceries',
                    responsible_party: 'Jane Doe',
                    amount: 45.67,
                },
            ],
            expectedPrefill: null,
        },
        {
            name: 'Multiple Line Items, First Match',
            lineItems: [
                {
                    _id: '5',
                    id: '5',
                    date: 1630329600,
                    payment_method: 'Credit Card',
                    description: 'Random Purchase',
                    responsible_party: 'John Doe',
                    amount: 15.0,
                },
                {
                    _id: '6',
                    id: '6',
                    date: 1630416000,
                    payment_method: 'Credit Card',
                    description: 'Spotify Family Plan',
                    responsible_party: 'Jane Doe',
                    amount: 14.99,
                },
                {
                    _id: '3',
                    id: '3',
                    date: 1630156800,
                    payment_method: 'Cash',
                    description: 'Furniture Purchase',
                    responsible_party: 'John Doe',
                    amount: 299.99,
                },
            ],
            expectedPrefill: { name: 'Spotify', category: 'Subscription' },
        },
    ];

    test.each(testCases)('$name', ({ lineItems, expectedPrefill }) => {
        expect(getPrefillFromLineItems(lineItems)).toEqual(expectedPrefill);
    });
});
