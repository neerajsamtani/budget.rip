import React from 'react';
import { render } from '../../../utils/test-utils';
import { Skeleton } from '../skeleton';

describe('Skeleton', () => {
  describe('Rendering', () => {
    it('renders the skeleton component', () => {
      const { container } = render(<Skeleton />);
      const skeleton = container.querySelector('[data-slot="skeleton"]');
      expect(skeleton).toBeInTheDocument();
    });

    it('applies default classes', () => {
      const { container } = render(<Skeleton />);
      const skeleton = container.querySelector('[data-slot="skeleton"]');
      expect(skeleton).toHaveClass('bg-accent', 'animate-pulse', 'rounded-md');
    });

    it('applies custom className', () => {
      const { container } = render(<Skeleton className="custom-class h-4 w-20" />);
      const skeleton = container.querySelector('[data-slot="skeleton"]');
      expect(skeleton).toHaveClass('custom-class', 'h-4', 'w-20');
    });

    it('merges custom classes with default classes', () => {
      const { container } = render(<Skeleton className="bg-primary" />);
      const skeleton = container.querySelector('[data-slot="skeleton"]');
      // Should have animate-pulse and rounded-md from defaults
      expect(skeleton).toHaveClass('animate-pulse', 'rounded-md');
    });
  });

  describe('Props Forwarding', () => {
    it('forwards additional props to the div element', () => {
      const { container } = render(<Skeleton data-testid="test-skeleton" />);
      expect(container.querySelector('[data-testid="test-skeleton"]')).toBeInTheDocument();
    });

    it('supports aria attributes', () => {
      const { container } = render(<Skeleton aria-label="Loading content" />);
      const skeleton = container.querySelector('[data-slot="skeleton"]');
      expect(skeleton).toHaveAttribute('aria-label', 'Loading content');
    });
  });
});
