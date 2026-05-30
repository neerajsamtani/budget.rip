import userEvent from '@testing-library/user-event';
import React from 'react';
import { useCreateSplitwiseExpense, useSplitwiseCurrentUser, useSplitwiseFriends } from '../../hooks/useApi';
import { render, screen, waitFor } from '../../utils/test-utils';
import { showErrorToast } from '../../utils/toast-helpers';
import CreateSplitwiseExpenseModal from '../CreateSplitwiseExpenseModal';

jest.mock('../../hooks/useApi', () => ({
  useCreateSplitwiseExpense: jest.fn(),
  useSplitwiseCurrentUser: jest.fn(),
  useSplitwiseFriends: jest.fn(),
}));

jest.mock('../../utils/toast-helpers', () => ({
  showErrorToast: jest.fn(),
  showSuccessToast: jest.fn(),
}));

const mockUseSplitwiseFriends = useSplitwiseFriends as jest.MockedFunction<typeof useSplitwiseFriends>;
const mockUseSplitwiseCurrentUser = useSplitwiseCurrentUser as jest.MockedFunction<typeof useSplitwiseCurrentUser>;
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
    mockUseSplitwiseCurrentUser.mockReturnValue({
      data: { id: 1 },
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
        split_method: 'equal',
        owed_shares: null,
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

  it('waits for the current Splitwise user before enabling creation', () => {
    mockUseSplitwiseCurrentUser.mockReturnValue({
      isLoading: true,
      isError: false,
    } as any);

    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    expect(screen.queryByText('Alice Smith')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Expense' })).toBeDisabled();
  });

  it('shows an error when the current Splitwise user fails to load', async () => {
    mockUseSplitwiseCurrentUser.mockReturnValue({
      isLoading: false,
      isError: true,
    } as any);

    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    await waitFor(() => expect(showErrorToast).toHaveBeenCalledWith('Failed to load Splitwise data.'));
  });

  it('switches from equal to custom mode and renders participant shares', async () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    await userEvent.click(screen.getByText('Alice Smith'));
    await userEvent.click(screen.getByRole('button', { name: 'Custom' }));

    expect(screen.getByLabelText('You owed share')).toBeInTheDocument();
    expect(screen.getByLabelText('Alice Smith owed share')).toBeInTheDocument();
    expect(screen.getByText('Remaining: $42.35')).toBeInTheDocument();
  });

  it('keeps custom creation disabled until shares allocate the full amount', async () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    await userEvent.click(screen.getByText('Alice Smith'));
    await userEvent.click(screen.getByRole('button', { name: 'Custom' }));
    await userEvent.type(screen.getByLabelText('You owed share'), '20');

    expect(screen.getByText('Remaining: $22.35')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Expense' })).toBeDisabled();

    await userEvent.type(screen.getByLabelText('Alice Smith owed share'), '22.35');

    expect(screen.getByText('Remaining: $0.00')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Expense' })).toBeEnabled();
  });

  it('creates a Splitwise expense with custom owed shares', async () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    await userEvent.click(screen.getByText('Alice Smith'));
    await userEvent.click(screen.getByRole('button', { name: 'Custom' }));
    await userEvent.type(screen.getByLabelText('You owed share'), '20');
    await userEvent.type(screen.getByLabelText('Alice Smith owed share'), '22.35');
    await userEvent.click(screen.getByRole('button', { name: 'Create Expense' }));

    expect(mutate).toHaveBeenCalledWith(
      {
        description: 'Trader Joes',
        amount: 42.35,
        friend_ids: [123],
        split_method: 'custom',
        owed_shares: { '1': 20, '123': 22.35 },
        date: '2024-01-15',
        currency_code: 'USD',
      },
      expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      })
    );
  });

  it('clears a custom share when its friend is removed', async () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    await userEvent.click(screen.getByText('Alice Smith'));
    await userEvent.click(screen.getByRole('button', { name: 'Custom' }));
    await userEvent.type(screen.getByLabelText('Alice Smith owed share'), '22.35');
    await userEvent.click(screen.getAllByText('Alice Smith')[0]);
    await userEvent.click(screen.getAllByText('Alice Smith')[0]);

    expect(screen.getByLabelText('Alice Smith owed share')).toHaveValue(null);
  });

  it('disables creation when the amount is invalid', async () => {
    render(<CreateSplitwiseExpenseModal show={true} onHide={onHide} selectedLineItems={selectedLineItems} />);

    await userEvent.click(screen.getByText('Alice Smith'));
    await userEvent.clear(screen.getByLabelText('Amount'));
    await userEvent.type(screen.getByLabelText('Amount'), 'e');

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
