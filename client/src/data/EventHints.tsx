import { Category } from "../components/CategoryFilter";
import { LineItemInterface } from "../contexts/LineItemsContext";

// TODO: Remove "any" types

// Basic CEL Evaluator
function evaluateCEL(expression: string, context: LineItemInterface) {
    // Helper function to safely get nested properties
    const getNestedProperty = (obj: any, path: string) => {
        return path.split('.').reduce((acc, part) => acc && acc[part], obj);
    };

    // Helper function to evaluate a single condition
    const evaluateCondition = (left: any, operator: any, right: any) => {
        switch (operator) {
            case '==': return left === right;
            case '!=': return left !== right;
            case '>': return left > right;
            case '<': return left < right;
            case '>=': return left >= right;
            case '<=': return left <= right;
            case 'in': return right.includes(left);
            case 'contains': return left.toLowerCase().includes(right.toLowerCase());
            default: throw new Error(`Unsupported operator: ${operator}`);
        }
    };

    // Split the expression into conditions
    const conditions = expression.split('&&').map(cond => cond.trim());

    // Evaluate each condition
    return conditions.every(condition => {
        const [left, operator, ...rightParts] = condition.split(/\s+/);
        const leftValue = getNestedProperty(context, left);
        let rightValue: any = rightParts.join(' ').replace(/^["']|["']$/g, '');

        // Try to parse the right value as a number or boolean
        if (rightValue === 'true') rightValue = true;
        else if (rightValue === 'false') rightValue = false;
        else if (!isNaN(rightValue)) rightValue = parseFloat(rightValue);

        return evaluateCondition(leftValue, operator, rightValue);
    });
}

// Event hints
type EventHint = {
    cel_expression: string,
    prefill: {
        name: string,
        category: Category
    }
}

const eventHints: EventHint[] = [
    {
        cel_expression: 'description contains "Spotify"',
        prefill: {
            name: "Spotify",
            category: "Subscription",
        }
    },
    {
        cel_expression: 'description contains "AMC" && amount == 23.95',
        prefill: {
            name: "AMC A-List",
            category: "Subscription",
        }
    },
    {
        cel_expression: 'description contains "ORIG CO NAME:Stripe, Inc" && amount > 2000.00',
        prefill: {
            name: "Paycheck",
            category: "Income",
        }
    },
    {
        cel_expression: 'description contains "BILT EQUITY RESIDE" && amount > 4000.00',
        prefill: {
            name: "Rent",
            category: "Rent",
        }
    },
    {
        cel_expression: 'description contains "ATT* BILL PAYMENT" && amount > 70.00',
        prefill: {
            name: "Phone Bill",
            category: "Subscription",
        }
    },
    {
        cel_expression: 'description contains "APPLE.COM/BILL" && amount == 0.99',
        prefill: {
            name: "iCloud+",
            category: "Subscription",
        }
    },
    {
        cel_expression: 'description contains "APPLE.COM/BILL" && amount == 0.99',
        prefill: {
            name: "iCloud+",
            category: "Subscription",
        }
    },
    {
        cel_expression: 'description contains "Internet" && amount < 70.00',
        prefill: {
            name: "Internet",
            category: "Rent",
        }
    },
    {
        cel_expression: 'description contains "Uber" && amount < 50.00',
        prefill: {
            name: "Uber",
            category: "Transit",
        }
    },
    {
        cel_expression: 'description contains "PGANDE CO" && amount > 70.00',
        prefill: {
            name: "PG&E",
            category: "Rent",
        }
    },
    {
        cel_expression: 'description contains "Supercuts" && amount > 30.00',
        prefill: {
            name: "Haircut",
            category: "Subscription",
        }
    },
    {
        cel_expression: 'description contains "Amazon Prime" && amount < 17.00 && amount > 16.00',
        prefill: {
            name: "Amazon Prime",
            category: "Subscription",
        }
    },
    {
        cel_expression: 'description contains "Trader Joe"',
        prefill: {
            name: "Trader Joes",
            category: "Groceries",
        }
    },
    {
        cel_expression: 'description contains "CHAAT CORNER INDIAN GROC"',
        prefill: {
            name: "Chaat Corner Indian Groceries",
            category: "Groceries",
        }
    },
    {
        cel_expression: 'description contains "CHAAT CORNER"',
        prefill: {
            name: "Chaat Corner",
            category: "Dining",
        }
    },
    {
        cel_expression: 'description contains "AMC 9640 ONLINE" && amount < 25.00 && amount > 24.00',
        prefill: {
            name: "AMC A-List",
            category: "Subscription",
        }
    }
];

export function getPrefillFromLineItems(lineItems: LineItemInterface[]) {
    if (!lineItems || lineItems.length === 0) {
        return null;
    }

    for (const hint of eventHints) {
        const isMatch = lineItems.some(lineItem =>
            evaluateCEL(hint.cel_expression, lineItem)
        );

        if (isMatch) {
            return hint.prefill;
        }
    }

    return null;
}

// Test function
type TestCase = {
    name: string,
    lineItems: LineItemInterface[],
    expectedPrefill: object | null
}

function testPrefillFromLineItems() {
    const testCases: TestCase[] = [
        {
            name: "Spotify Subscription",
            lineItems: [
                {
                    _id: "1",
                    id: "1",
                    date: 1629984000,
                    payment_method: "Credit Card",
                    description: "Spotify Premium Subscription",
                    responsible_party: "John Doe",
                    amount: 9.99,
                }
            ],
            expectedPrefill: { name: "Spotify", category: "Subscription" }
        },
        {
            name: "AMC A-List Subscription",
            lineItems: [
                {
                    _id: "2",
                    id: "2",
                    date: 1630070400,
                    payment_method: "Credit Card",
                    description: "AMC A-List Monthly Subscription",
                    responsible_party: "Jane Doe",
                    amount: 23.95,
                }
            ],
            expectedPrefill: { name: "AMC A-List", category: "Subscription" }
        },
        {
            name: "Large Cash Purchase",
            lineItems: [
                {
                    _id: "3",
                    id: "3",
                    date: 1630156800,
                    payment_method: "Cash",
                    description: "Furniture Purchase",
                    responsible_party: "John Doe",
                    amount: 299.99,
                }
            ],
            expectedPrefill: { name: "Large Cash Purchase", category: "Expense" }
        },
        {
            name: "No Match",
            lineItems: [
                {
                    _id: "4",
                    id: "4",
                    date: 1630243200,
                    payment_method: "Credit Card",
                    description: "Groceries",
                    responsible_party: "Jane Doe",
                    amount: 45.67,
                }
            ],
            expectedPrefill: null
        },
        {
            name: "Multiple Line Items, First Match",
            lineItems: [
                {
                    _id: "5",
                    id: "5",
                    date: 1630329600,
                    payment_method: "Credit Card",
                    description: "Random Purchase",
                    responsible_party: "John Doe",
                    amount: 15.00,
                },
                {
                    _id: "6",
                    id: "6",
                    date: 1630416000,
                    payment_method: "Credit Card",
                    description: "Spotify Family Plan",
                    responsible_party: "Jane Doe",
                    amount: 14.99,
                },
                {
                    _id: "3",
                    id: "3",
                    date: 1630156800,
                    payment_method: "Cash",
                    description: "Furniture Purchase",
                    responsible_party: "John Doe",
                    amount: 299.99,
                },
            ],
            expectedPrefill: { name: "Spotify", category: "Subscription" }
        }
    ];

    testCases.forEach(testCase => {
        const result = getPrefillFromLineItems(testCase.lineItems);
        console.log(`Test Case: ${testCase.name}`);
        console.log(`Expected: ${JSON.stringify(testCase.expectedPrefill)}`);
        console.log(`Actual: ${JSON.stringify(result)}`);
        console.log(`Result: ${JSON.stringify(result) === JSON.stringify(testCase.expectedPrefill) ? 'PASS' : 'FAIL'}`);
        console.log('---');
    });
}
