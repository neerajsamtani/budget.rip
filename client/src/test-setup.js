// Suppress Node.js deprecation warnings during tests
process.env.NODE_NO_WARNINGS = '1';

// Suppress specific deprecation warnings
const originalEmitWarning = process.emitWarning;
process.emitWarning = (...args) => {
    if (args[2] === 'DEP0040') {
        // Suppress punycode deprecation warnings
        return;
    }
    return originalEmitWarning.apply(process, args);
}; 