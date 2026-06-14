# Frontend Testing Guide

This guide covers the testing setup and best practices for the Budgit frontend application.

## 🧪 Testing Stack

- **Jest**: Test runner and assertion library
- **React Testing Library**: Modern React testing utilities
- **@testing-library/jest-dom**: Custom Jest matchers for DOM testing
- **@testing-library/user-event**: Simulate user interactions
- **MSW**: Mock Service Worker for API mocking

## 📁 Test Structure

```
src/
├── __tests__/           # Test files
│   ├── components/      # Component tests
│   ├── pages/          # Page tests
│   ├── utils/          # Utility function tests
│   └── hooks/          # Custom hook tests
├── setupTests.ts       # Global test setup
└── utils/
    └── test-utils.tsx  # Custom test utilities
```

## 🎯 Testing Philosophy

### 1. Test Behavior, Not Implementation
```typescript
// ❌ Bad - Testing implementation details
expect(component.state.isOpen).toBe(true);

// ✅ Good - Testing user-visible behavior
expect(screen.getByRole('dialog')).toBeInTheDocument();
```

### 2. Use Semantic Queries
```typescript
// ❌ Bad - Fragile selectors
screen.getByTestId('submit-button');

// ✅ Good - Semantic queries
screen.getByRole('button', { name: /submit/i });
screen.getByLabelText('Email address');
screen.getByPlaceholderText('Enter your email');
```

### 3. Test User Interactions
```typescript
// ✅ Good - Test what users actually do
const user = userEvent.setup();
await user.click(screen.getByRole('button', { name: /submit/i }));
await user.type(screen.getByLabelText('Email'), 'test@example.com');
```

## 🚀 Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- LineItem.test.tsx

# Run tests matching a pattern
npm test -- --testNamePattern="renders"
```

## 📝 Writing Tests

### Component Test Example

```typescript
import React from 'react';
import { render, screen } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByRole('heading')).toHaveTextContent('My Component');
  });

  it('handles user interactions', async () => {
    const user = userEvent.setup();
    render(<MyComponent />);

    const button = screen.getByRole('button', { name: /click me/i });
    await user.click(button);

    expect(screen.getByText('Clicked!')).toBeInTheDocument();
  });
});
```

### Testing with Context

```typescript
// Mock the context
jest.mock('../contexts/MyContext', () => ({
  useMyContext: jest.fn(),
}));

import { useMyContext } from '../contexts/MyContext';

const mockUseMyContext = useMyContext as jest.MockedFunction<typeof useMyContext>;

describe('ComponentWithContext', () => {
  beforeEach(() => {
    mockUseMyContext.mockReturnValue({ data: 'test' });
  });

  it('uses context data', () => {
    render(<ComponentWithContext />);
    expect(screen.getByText('test')).toBeInTheDocument();
  });
});
```

### Testing API Calls

```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/data', (req, res, ctx) => {
    return res(ctx.json({ data: 'test' }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

it('fetches and displays data', async () => {
  render(<DataComponent />);

  await waitFor(() => {
    expect(screen.getByText('test')).toBeInTheDocument();
  });
});
```

## 🎨 Testing Best Practices

### 1. Test Organization
```typescript
describe('ComponentName', () => {
  describe('Rendering', () => {
    it('renders correctly', () => {});
    it('shows loading state', () => {});
  });

  describe('User Interactions', () => {
    it('handles button clicks', () => {});
    it('handles form submissions', () => {});
  });

  describe('Error Handling', () => {
    it('shows error message', () => {});
    it('handles network errors', () => {});
  });
});
```

### 2. Test Data
```typescript
// Use consistent mock data
export const mockUser = {
  id: '1',
  name: 'John Doe',
  email: 'john@example.com',
};

// Create factories for complex data
export const createMockUser = (overrides = {}) => ({
  ...mockUser,
  ...overrides,
});
```

### 3. Async Testing
```typescript
it('loads data asynchronously', async () => {
  render(<AsyncComponent />);

  // Wait for loading to complete
  await waitFor(() => {
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });

  expect(screen.getByText('Data loaded')).toBeInTheDocument();
});
```

### 4. Accessibility Testing
```typescript
it('is accessible', () => {
  render(<MyComponent />);

  // Check for proper heading structure
  expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();

  // Check for proper form labels
  expect(screen.getByLabelText('Email')).toBeInTheDocument();

  // Check for proper button labels
  expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
});
```

## 🔧 Custom Test Utilities

### Custom Render Function
```typescript
// utils/test-utils.tsx
const AllTheProviders = ({ children }) => (
  <BrowserRouter>
    <MyProvider>
      {children}
    </MyProvider>
  </BrowserRouter>
);

const customRender = (ui, options = {}) =>
  render(ui, { wrapper: AllTheProviders, ...options });

export { customRender as render };
```

### Mock Data
```typescript
export const mockLineItem = {
  id: '1',
  date: 1640995200,
  payment_method: 'credit_card',
  description: 'Test transaction',
  responsible_party: 'Test Store',
  amount: 50.00,
  isSelected: false,
};
```

## 📊 Coverage Goals

- **Statements**: 80%
- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%

## 🐛 Debugging Tests

### Common Issues

1. **Async Operations**: Use `waitFor` for async operations
2. **Mocking**: Ensure mocks are set up before imports
3. **Context**: Mock context providers properly
4. **Event Listeners**: Clean up event listeners in `afterEach`

### Debug Commands
```bash
# Run tests with verbose output
npm test -- --verbose

# Run tests with console.log output
npm test -- --verbose --no-coverage

# Debug specific test
npm test -- --testNamePattern="specific test name"
```

## 📚 Additional Resources

- [React Testing Library Documentation](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [MSW Documentation](https://mswjs.io/docs/)

## 🤝 Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain good test coverage
4. Follow the testing patterns established in this guide
5. Update this documentation if needed
