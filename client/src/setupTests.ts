// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';



// Suppress console logs during tests to reduce noise
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

beforeAll(() => {
    // Suppress console.log and console.error during tests
    console.log = jest.fn();
    console.error = jest.fn();
});

afterAll(() => {
    // Restore original console methods
    console.log = originalConsoleLog;
    console.error = originalConsoleError;
});

// Mock IntersectionObserver if not available in test environment
(global as typeof globalThis).IntersectionObserver = class IntersectionObserver {
    readonly root: Element | null = null;
    readonly rootMargin: string = '';
    readonly thresholds: readonly number[] = [];
    constructor() { }
    disconnect() { }
    observe() { }
    unobserve() { }
    takeRecords(): IntersectionObserverEntry[] { return []; }
};

// Mock ResizeObserver if not available in test environment
(global as typeof globalThis).ResizeObserver = class ResizeObserver {
    constructor() { }
    disconnect() { }
    observe() { }
    unobserve() { }
};

// Mock MutationObserver if not available in test environment
(global as typeof globalThis).MutationObserver = class MutationObserver {
    constructor() { }
    disconnect() { }
    observe() { }
    takeRecords() { return []; }
};

// Answer width range queries such as "(width >= 80rem)" from window.innerWidth, which tests set
// with setViewportWidth; every other query doesn't match.
function matchesWidthQuery(query: string) {
    const match = /^\(width (>=|<) ([\d.]+)(px|rem)\)$/.exec(query);
    if (!match) return false;
    const breakpoint = Number(match[2]) * (match[3] === 'rem' ? 16 : 1);
    return match[1] === '>=' ? window.innerWidth >= breakpoint : window.innerWidth < breakpoint;
}

// Restore jsdom's default width so one test's viewport doesn't leak into the next.
const defaultInnerWidth = window.innerWidth;
afterEach(() => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: defaultInnerWidth });
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
        matches: matchesWidthQuery(query),
        media: query,
        onchange: null,
        addListener: jest.fn(), // deprecated
        removeListener: jest.fn(), // deprecated
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});
