const tsJest = require('ts-jest').default;

const transformer = tsJest.createTransformer({
  compilerOptions: {
    module: 'commonjs'
  }
});

module.exports = {
  process(src, filename, options) {
    // Transform import.meta.env to process.env for Jest
    const transformedSrc = src.replace(
      /import\.meta\.env\.VITE_(\w+)/g,
      'process.env.VITE_$1'
    );

    return transformer.process(transformedSrc, filename, options);
  }
};