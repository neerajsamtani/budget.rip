// Import any string helper functions you have
// For now, let's create a simple test structure

describe('String Helpers', () => {
    it('should format currency correctly', () => {
        // Example test - you can adapt this to your actual string helper functions
        const formatCurrency = (amount: number): string => {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
            }).format(amount);
        };

        expect(formatCurrency(1234.56)).toBe('$1,234.56');
        expect(formatCurrency(0)).toBe('$0.00');
        expect(formatCurrency(100)).toBe('$100.00');
    });

    it('should capitalize first letter', () => {
        const capitalize = (str: string): string => {
            return str.charAt(0).toUpperCase() + str.slice(1);
        };

        expect(capitalize('hello')).toBe('Hello');
        expect(capitalize('world')).toBe('World');
        expect(capitalize('')).toBe('');
    });

    it('should truncate long strings', () => {
        const truncate = (str: string, maxLength: number): string => {
            if (str.length <= maxLength) return str;
            return str.slice(0, maxLength) + '...';
        };

        expect(truncate('Hello World', 5)).toBe('Hello...');
        expect(truncate('Short', 10)).toBe('Short');
        expect(truncate('', 5)).toBe('');
    });
}); 