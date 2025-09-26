import tsJest from 'ts-jest';

const transformer = tsJest.default.createTransformer({
  compilerOptions: {
    module: 'commonjs'
  }
});

export default {
  process(src, filename, options) {
    // Transform import.meta.env to process.env for Jest
    const transformedSrc = src.replace(
      /import\.meta\.env\.VITE_(\w+)/g,
      'process.env.VITE_$1'
    );

    return transformer.process(transformedSrc, filename, options);
  }
};