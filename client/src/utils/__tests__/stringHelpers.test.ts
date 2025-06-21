import defaultNameCleanup from '../stringHelpers';

describe('String Helpers', () => {
    describe('defaultNameCleanup', () => {
        it('removes SQ * prefix', () => {
            expect(defaultNameCleanup('SQ *TEST STORE')).toBe('Test Store');
        });

        it('removes TST* prefix', () => {
            expect(defaultNameCleanup('TST* TEST STORE')).toBe('Test Store');
        });

        it('returns original string when no prefix matches', () => {
            expect(defaultNameCleanup('TEST STORE')).toBe('Test Store');
        });

        it('handles empty string', () => {
            expect(defaultNameCleanup('')).toBe('');
        });

        it('handles string with only whitespace', () => {
            expect(defaultNameCleanup('   ')).toBe('');
        });

        it('converts to title case', () => {
            expect(defaultNameCleanup('hello world')).toBe('Hello World');
            expect(defaultNameCleanup('HELLO WORLD')).toBe('Hello World');
            expect(defaultNameCleanup('hElLo WoRlD')).toBe('Hello World');
        });

        it('removes special characters except alphanumeric, spaces, hyphens, and ampersands', () => {
            expect(defaultNameCleanup('TEST@STORE!')).toBe('Teststore');
            expect(defaultNameCleanup('TEST-STORE')).toBe('test-store');
            expect(defaultNameCleanup('TEST & STORE')).toBe('Test & Store');
            expect(defaultNameCleanup('TEST_STORE')).toBe('Teststore');
        });

        it('handles multiple spaces', () => {
            expect(defaultNameCleanup('TEST   STORE')).toBe('Test   Store');
        });

        it('handles leading and trailing spaces', () => {
            expect(defaultNameCleanup('  TEST STORE  ')).toBe('Test Store');
        });

        it('handles mixed case with special characters', () => {
            expect(defaultNameCleanup('SQ *tEsT@sToRe!')).toBe('Teststore');
        });

        it('handles numbers in the string', () => {
            expect(defaultNameCleanup('TEST STORE 123')).toBe('Test Store 123');
            expect(defaultNameCleanup('123 TEST STORE')).toBe('123 Test Store');
        });

        it('handles complex real-world examples', () => {
            expect(defaultNameCleanup('SQ *STARBUCKS COFFEE')).toBe('Starbucks Coffee');
            expect(defaultNameCleanup('TST* AMAZON.COM')).toBe('Amazoncom');
            expect(defaultNameCleanup('WALMART SUPERCENTER #1234')).toBe('Walmart Supercenter 1234');
        });

        it('handles strings with only special characters', () => {
            expect(defaultNameCleanup('!@#$%^&*()')).toBe('&');
        });

        it('handles strings with only numbers', () => {
            expect(defaultNameCleanup('123456')).toBe('123456');
        });

        it('handles single character strings', () => {
            expect(defaultNameCleanup('A')).toBe('A');
            expect(defaultNameCleanup('a')).toBe('A');
            expect(defaultNameCleanup('1')).toBe('1');
        });

        it('handles strings with ampersands', () => {
            expect(defaultNameCleanup('BARNES & NOBLE')).toBe('Barnes & Noble');
            expect(defaultNameCleanup('AT&T STORE')).toBe('at&t Store');
        });

        it('handles strings with hyphens', () => {
            expect(defaultNameCleanup('CVS-PHARMACY')).toBe('cvs-pharmacy');
            expect(defaultNameCleanup('7-ELEVEN')).toBe('7-eleven');
        });

        it('handles single character', () => {
            expect(defaultNameCleanup('A')).toBe('A');
        });

        it('handles numbers', () => {
            expect(defaultNameCleanup('123')).toBe('123');
        });

        it('handles mixed case', () => {
            expect(defaultNameCleanup('TeSt StOrE')).toBe('Test Store');
        });

        it('handles strings with special characters', () => {
            expect(defaultNameCleanup('TEST@STORE!')).toBe('Teststore');
            expect(defaultNameCleanup('TEST#STORE$')).toBe('Teststore');
            expect(defaultNameCleanup('TEST%STORE^')).toBe('Teststore');
        });

        it('handles strings with underscores', () => {
            expect(defaultNameCleanup('TEST_STORE')).toBe('Teststore');
            expect(defaultNameCleanup('TEST__STORE')).toBe('Teststore');
        });
    });
}); 