module.exports = {
    // The test environment that will be used for testing
    testEnvironment: 'jsdom',

    // The glob patterns Jest uses to detect test files
    testMatch: [
        '**/__tests__/**/*.(ts|tsx|js)',
        '**/*.(test|spec).(ts|tsx|js)'
    ],

    // An array of file extensions your modules use
    moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

    // A map from regular expressions to paths to transformers
    transform: {
        '^.+\\.(ts|tsx)$': 'ts-jest',
        '^.+\\.(js|jsx)$': 'babel-jest',
    },

    // An array of regexp pattern strings that are matched against all test paths, matched tests are skipped
    testPathIgnorePatterns: [
        '/node_modules/',
        '/build/',
        '/dist/'
    ],

    // The directory where Jest should output its coverage files
    coverageDirectory: 'coverage',

    // An array of glob patterns indicating a set of files for which coverage information should be collected
    collectCoverageFrom: [
        'src/**/*.{ts,tsx}',
        '!src/**/*.d.ts',
        '!src/index.js',
        '!src/setupTests.ts'
    ],

    // A list of reporter names that Jest uses when writing coverage reports
    coverageReporters: ['text', 'lcov', 'html'],

    // The test environment options that will be passed to the testEnvironment
    testEnvironmentOptions: {
        url: 'http://localhost'
    },

    // Setup files that will be run before each test
    setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],

    // Module name mapping for absolute imports
    moduleNameMapping: {
        '^@/(.*)$': '<rootDir>/src/$1'
    },

    // Indicates whether the coverage information should be collected while executing the test
    collectCoverage: false,

    // The maximum amount of workers used to run your tests
    maxWorkers: '50%',

    // Automatically clear mock calls and instances between every test
    clearMocks: true,

    // Indicates whether each individual test should be reported during the run
    verbose: true,

    // Force Jest to exit after all tests complete
    forceExit: true,

    // Transform ignore patterns
    transformIgnorePatterns: [
        'node_modules/(?!(axios)/)'
    ],

    // Extensions to treat as ES modules
    extensionsToTreatAsEsm: ['.ts', '.tsx']
}; 