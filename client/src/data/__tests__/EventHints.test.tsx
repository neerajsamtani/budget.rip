import { getPrefillFromLineItems } from '../EventHints';

describe('getPrefillFromLineItems', () => {
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

    testCases.forEach(({ name, lineItems, expectedPrefill }) => {
        it(`should return correct prefill for: ${name}`, () => {
            expect(getPrefillFromLineItems(lineItems)).toEqual(expectedPrefill);
        });
    });
}); 