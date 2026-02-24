import React from 'react';
import { render, screen } from '../../utils/test-utils';
import { SpendingTooltipContent } from '../charts/ChartTooltip';

function makePayloadItem(name: string, value: number) {
  return { name, value, dataKey: name, color: '#000000' };
}

describe('SpendingTooltipContent', () => {
  it('returns null when active is false', () => {
    const { container } = render(
      <SpendingTooltipContent active={false} payload={[makePayloadItem('Dining', 100)]} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('returns null when all payload values are zero', () => {
    const { container } = render(
      <SpendingTooltipContent active={true} payload={[makePayloadItem('Dining', 0)]} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('items are sorted alphabetically by name', () => {
    const { container } = render(
      <SpendingTooltipContent
        active={true}
        payload={[makePayloadItem('Zucchini', 200), makePayloadItem('Apple', 100)]}
      />
    );
    const { innerHTML } = container;
    expect(innerHTML.indexOf('Apple')).toBeLessThan(innerHTML.indexOf('Zucchini'));
  });

  it('Total row is shown when there are multiple non-zero items', () => {
    render(
      <SpendingTooltipContent
        active={true}
        payload={[makePayloadItem('Dining', 100), makePayloadItem('Shopping', 50)]}
      />
    );
    expect(screen.getByText('Total')).toBeInTheDocument();
  });

  it('Total row is hidden for a single item', () => {
    render(
      <SpendingTooltipContent
        active={true}
        payload={[makePayloadItem('Dining', 100)]}
      />
    );
    expect(screen.queryByText('Total')).toBeNull();
  });

  it('Total row is hidden when showTotal is false', () => {
    render(
      <SpendingTooltipContent
        active={true}
        payload={[makePayloadItem('Dining', 100), makePayloadItem('Shopping', 50)]}
        showTotal={false}
      />
    );
    expect(screen.queryByText('Total')).toBeNull();
  });
});
