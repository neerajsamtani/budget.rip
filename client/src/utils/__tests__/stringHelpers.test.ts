import defaultNameCleanup from '../stringHelpers';

describe('String Helpers', () => {
    describe('defaultNameCleanup', () => {
        it('SQ * prefix is removed', () => {
            expect(defaultNameCleanup('SQ *TEST STORE')).toBe('Test Store');
        });

        it('TST* prefix is removed', () => {
            expect(defaultNameCleanup('TST* TEST STORE')).toBe('Test Store');
        });

        it('original string is returned when no prefix matches', () => {
            expect(defaultNameCleanup('TEST STORE')).toBe('Test Store');
        });

        it('empty string is handled', () => {
            expect(defaultNameCleanup('')).toBe('');
        });

        it('string with only whitespace is handled', () => {
            expect(defaultNameCleanup('   ')).toBe('');
        });

        it('string is converted to title case', () => {
            expect(defaultNameCleanup('hello world')).toBe('Hello World');
            expect(defaultNameCleanup('HELLO WORLD')).toBe('Hello World');
            expect(defaultNameCleanup('hElLo WoRlD')).toBe('Hello World');
        });

        it('special characters are removed except alphanumeric, spaces, hyphens, and ampersands', () => {
            expect(defaultNameCleanup('TEST@STORE!')).toBe('Teststore');
            expect(defaultNameCleanup('TEST-STORE')).toBe('test-store');
            expect(defaultNameCleanup('TEST & STORE')).toBe('Test & Store');
            expect(defaultNameCleanup('TEST_STORE')).toBe('Teststore');
        });

        it('multiple spaces are handled', () => {
            expect(defaultNameCleanup('TEST   STORE')).toBe('Test   Store');
        });

        it('leading and trailing spaces are handled', () => {
            expect(defaultNameCleanup('  TEST STORE  ')).toBe('Test Store');
        });

        it('mixed case with special characters is handled', () => {
            expect(defaultNameCleanup('SQ *tEsT@sToRe!')).toBe('Teststore');
        });

        it('numbers in the string are handled', () => {
            expect(defaultNameCleanup('TEST STORE 123')).toBe('Test Store 123');
            expect(defaultNameCleanup('123 TEST STORE')).toBe('123 Test Store');
        });

        it('complex real-world examples are handled', () => {
            expect(defaultNameCleanup('SQ *STARBUCKS COFFEE')).toBe('Starbucks Coffee');
            expect(defaultNameCleanup('TST* AMAZON.COM')).toBe('Amazoncom');
            expect(defaultNameCleanup('WALMART SUPERCENTER #1234')).toBe('Walmart Supercenter 1234');
        });

        it('strings with only special characters are handled', () => {
            expect(defaultNameCleanup('!@#$%^&*()')).toBe('&');
        });

        it('strings with only numbers are handled', () => {
            expect(defaultNameCleanup('123456')).toBe('123456');
        });

        it('single character strings are handled', () => {
            expect(defaultNameCleanup('A')).toBe('A');
            expect(defaultNameCleanup('a')).toBe('A');
            expect(defaultNameCleanup('1')).toBe('1');
        });

        it('strings with ampersands are handled', () => {
            expect(defaultNameCleanup('BARNES & NOBLE')).toBe('Barnes & Noble');
            expect(defaultNameCleanup('AT&T STORE')).toBe('at&t Store');
        });

        it('strings with hyphens are handled', () => {
            expect(defaultNameCleanup('CVS-PHARMACY')).toBe('cvs-pharmacy');
            expect(defaultNameCleanup('7-ELEVEN')).toBe('7-eleven');
        });

        it('single character is handled', () => {
            expect(defaultNameCleanup('A')).toBe('A');
        });

        it('numbers are handled', () => {
            expect(defaultNameCleanup('123')).toBe('123');
        });

        it('mixed case is handled', () => {
            expect(defaultNameCleanup('TeSt StOrE')).toBe('Test Store');
        });

        it('strings with special characters are handled', () => {
            expect(defaultNameCleanup('TEST@STORE!')).toBe('Teststore');
            expect(defaultNameCleanup('TEST#STORE$')).toBe('Teststore');
            expect(defaultNameCleanup('TEST%STORE^')).toBe('Teststore');
        });

        it('strings with underscores are handled', () => {
            expect(defaultNameCleanup('TEST_STORE')).toBe('Teststore');
            expect(defaultNameCleanup('TEST__STORE')).toBe('Teststore');
        });
    });
}); 