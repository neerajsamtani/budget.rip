import userEvent from '@testing-library/user-event';
import React from 'react';
import { useCreateSplitwiseExpense, useSplitwiseFriends } from '../../hooks/useApi';
import { render, screen, waitFor } from '../../utils/test-utils';
import CreateSplitwiseExpenseModal from '../CreateSplitwiseExpenseModal';

jest.mock('../../hooks/useApi', () => ({
  useCreateSplitwiseExpense: jest.fn(),
  useSplitwiseFriends: jest.fn(),
}));

jest.mock('../../utils/toast-helpers', () => ({
  showErrorToast: jest.fn(),
  showSuccessToast: jest.fn(),
}));

const mockUseSplitwiseFriends = useSplitwiseFriends as jest.MockedFunction<typeof useSplitwiseFriends>;
const mockUseCreateSplitwiseExpense = useCreateSplitwiseExpense as jest.MockedFunction<typeof useCreateSplitwiseExpense>;

const selectedLineItems = [
  {
    id: 'li_1',
    date: 1705276800,
    payment_method: 'Credit Card',
    description: 'Trader Joes',
    responsible_party: 'Neeraj',
    amount: 42.35,
    isSelected: true,
  },
];

describe('CreateSplitwiseExpenseModal', () => {
  const mutate = jest.fn();
  const onHide = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSplitwiseFriends.mockReturnValue({
      data: [{ id: 123, first_name: 'Alice', last_name: 'Smith', name: 'Alice Smith' }],
      isLoading: false,
      isError: false,
    } as any);
    mockUseCreateSplitwiseExpense.mockReturnValue({
      mutate,
      isPending: false,
    } as any);
  });

  it('prefills fields from the selected line item', () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    expect(screen.getByRole('heading', { name: 'New Splitwise Expense' })).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toHaveValue('Trader Joes');
    expect(screen.getByLabelText('Amount')).toHaveValue(42.35);
    expect(screen.getByLabelText('Date')).toHaveValue('2024-01-15');
    expect(screen.getByText('Selected total: $42.35')).toBeInTheDocument();
  });

  it('creates a Splitwise expense with selected friends', async () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    await userEvent.click(screen.getByText('Alice Smith'));
    await userEvent.click(screen.getByRole('button', { name: 'Create Expense' }));

    expect(mutate).toHaveBeenCalledWith(
      {
        description: 'Trader Joes',
        amount: 42.35,
        friend_ids: [123],
        date: '2024-01-15',
        currency_code: 'USD',
      },
      expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      })
    );
  });

  it('disables creation until a friend is selected', () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    expect(screen.getByRole('button', { name: 'Create Expense' })).toBeDisabled();
  });

  it('remounts with fresh defaults when selected line items change', async () => {
    const { rerender } = render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);
    await userEvent.clear(screen.getByLabelText('Description'));
    await userEvent.type(screen.getByLabelText('Description'), 'Edited');

    rerender(
      <CreateSplitwiseExpenseModal
        show={true}
        onHide={onHide}
        selectedLineItems={[{ ...selectedLineItems[0], id: 'li_2', description: 'Dinner', amount: 18 }]}
      />
    );

    expect(screen.getByLabelText('Description')).toHaveValue('Dinner');
    expect(screen.getByLabelText('Amount')).toHaveValue(18);
  });

  it('closes after a successful create', async () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    await userEvent.click(screen.getByText('Alice Smith'));
    await userEvent.click(screen.getByRole('button', { name: 'Create Expense' }));
    const callbacks = mutate.mock.calls[0][1];
    callbacks.onSuccess();

    await waitFor(() => expect(onHide).toHaveBeenCalled());
  });
});
