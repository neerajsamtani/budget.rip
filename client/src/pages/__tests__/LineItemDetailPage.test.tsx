import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { createTestQueryClient, mockAxiosInstance } from '../../utils/test-utils';
import LineItemDetailPage from '../LineItemDetailPage';

jest.mock('sonner', () => {
    const mockToast = jest.fn();
    return {
        toast: Object.assign(mockToast, {
            success: jest.fn(),
            error: jest.fn(),
            warning: jest.fn(),
            info: jest.fn(),
        }),
    };
});

const manualLineItem = {
    id: 'line-1',
    transaction_id: 'txn-1',
    date: 1640995200,
    payment_method_id: 'pm_cash',
    payment_method: 'Cash',
    description: 'Coffee',
    responsible_party: 'Cafe',
    amount: 4.5,
    notes: 'Morning',
    is_manual: true,
};

const syncedLineItem = {
    ...manualLineItem,
    id: 'line-synced',
    transaction_id: 'txn-synced',
    is_manual: false,
};

const assignedManualLineItem = {
    ...manualLineItem,
    id: 'line-assigned',
    event_id: 'event-1',
};

const paymentMethods = [
    { id: 'pm_cash', name: 'Cash', type: 'cash', is_active: true },
    { id: 'pm_venmo', name: 'Venmo', type: 'venmo', is_active: true },
];

function LocationProbe() {
    const location = useLocation();
    return <div data-testid="location">{location.pathname}{location.search}</div>;
}

function renderLineItemDetail(initialEntry = '/line_items/line-1?paymentMethod=Cash', initialEntries?: string[]) {
    const queryClient = createTestQueryClient();
    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter initialEntries={initialEntries || [initialEntry]} initialIndex={initialEntries ? initialEntries.length - 1 : 0}>
                <Routes>
                    <Route path="/line_items/:lineItemId" element={<><LineItemDetailPage /><LocationProbe /></>} />
                    <Route path="/line_items" element={<><div>Line Items List</div><LocationProbe /></>} />
                    <Route path="/" element={<><div>Review List</div><LocationProbe /></>} />
                    <Route path="/events/:eventId" element={<><div>Event Detail</div><LocationProbe /></>} />
                </Routes>
            </MemoryRouter>
        </QueryClientProvider>
    );
}

function mockApi(lineItem = manualLineItem) {
    mockAxiosInstance.get.mockImplementation((url: string) => {
        if (url.startsWith('api/line_items/')) {
            return Promise.resolve({ data: lineItem });
        }
        if (url === 'api/payment_methods') {
            return Promise.resolve({ data: { data: paymentMethods } });
        }
        return Promise.resolve({ data: { data: [] } });
    });
    mockAxiosInstance.put.mockResolvedValue({ data: { ...lineItem, description: 'Coffee beans' } });
    mockAxiosInstance.delete.mockResolvedValue({});
}

describe('LineItemDetailPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockApi();
    });

    it('fetches and renders line item details', async () => {
        renderLineItemDetail();

        await waitFor(() => expect(screen.getByRole('heading', { name: 'Coffee' })).toBeInTheDocument());

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('api/line_items/line-1');
        expect(screen.getByText('txn-1')).toBeInTheDocument();
        expect(screen.getByText('pm_cash')).toBeInTheDocument();
        expect(screen.getAllByText('Cash').length).toBeGreaterThan(0);
        expect(screen.getByText('Morning')).toBeInTheDocument();
    });

    it('updates a manual line item and stays on the detail route', async () => {
        renderLineItemDetail();

        await waitFor(() => expect(screen.getByRole('button', { name: /Edit/ })).toBeInTheDocument());
        await userEvent.click(screen.getByRole('button', { name: /Edit/ }));
        await userEvent.clear(screen.getByLabelText('Description'));
        await userEvent.type(screen.getByLabelText('Description'), 'Coffee beans');
        await userEvent.click(screen.getByRole('button', { name: /Save Changes/ }));

        await waitFor(() => {
            expect(mockAxiosInstance.put).toHaveBeenCalledWith('api/line_items/line-1', expect.objectContaining({
                description: 'Coffee beans',
                payment_method_id: 'pm_cash',
            }));
        });
        expect(screen.getByTestId('location')).toHaveTextContent('/line_items/line-1?paymentMethod=Cash');
    });

    it('deletes an unassigned manual line item and returns to the filtered list', async () => {
        renderLineItemDetail();

        await waitFor(() => expect(screen.getByRole('button', { name: /Delete/ })).toBeInTheDocument());
        await userEvent.click(screen.getByRole('button', { name: /Delete/ }));

        await waitFor(() => expect(mockAxiosInstance.delete).toHaveBeenCalledWith('api/manual_transaction/txn-1'));
        expect(screen.getByText('Line Items List')).toBeInTheDocument();
        expect(screen.getByTestId('location')).toHaveTextContent('/line_items?paymentMethod=Cash');
    });

    it('disables synced line item edit and delete actions with tooltip copy', async () => {
        mockApi(syncedLineItem);
        renderLineItemDetail('/line_items/line-synced');

        await waitFor(() => expect(screen.getByRole('button', { name: /Edit/ })).toBeDisabled());
        expect(screen.getByRole('button', { name: /Delete/ })).toBeDisabled();

        await userEvent.hover(screen.getByRole('button', { name: /Edit/ }).parentElement as HTMLElement);
        expect(await screen.findAllByText('Synced line items cannot be edited.')).not.toHaveLength(0);

        await userEvent.hover(screen.getByRole('button', { name: /Delete/ }).parentElement as HTMLElement);
        expect(await screen.findAllByText('Synced line items cannot be deleted.')).not.toHaveLength(0);
    });

    it('disables assigned manual line item delete with tooltip copy', async () => {
        mockApi(assignedManualLineItem);
        renderLineItemDetail('/line_items/line-assigned');

        await waitFor(() => expect(screen.getByRole('button', { name: /Edit/ })).toBeEnabled());
        expect(screen.getByRole('button', { name: /Delete/ })).toBeDisabled();

        await userEvent.hover(screen.getByRole('button', { name: /Delete/ }).parentElement as HTMLElement);
        expect(await screen.findAllByText('Remove this line item from its event before deleting it.')).not.toHaveLength(0);
    });

    it('falls back to line item list filters when there is no route history', async () => {
        renderLineItemDetail('/line_items/line-1?paymentMethod=Cash');

        await waitFor(() => expect(screen.getByRole('button', { name: /Line Items/ })).toBeInTheDocument());
        await userEvent.click(screen.getByRole('button', { name: /Line Items/ }));

        expect(screen.getByText('Line Items List')).toBeInTheDocument();
        expect(screen.getByTestId('location')).toHaveTextContent('/line_items?paymentMethod=Cash');
    });

    it('uses browser-style back navigation when opened from review', async () => {
        renderLineItemDetail(
            `/line_items/line-1?returnTo=${encodeURIComponent('/')}`,
            ['/', `/line_items/line-1?returnTo=${encodeURIComponent('/')}`],
        );

        await waitFor(() => expect(screen.getByRole('button', { name: /Review/ })).toBeInTheDocument());
        await userEvent.click(screen.getByRole('button', { name: /Review/ }));

        expect(screen.getByText('Review List')).toBeInTheDocument();
        expect(screen.getByTestId('location')).toHaveTextContent('/');
    });

    it('returns to review after deleting when opened from review', async () => {
        renderLineItemDetail(`/line_items/line-1?returnTo=${encodeURIComponent('/')}`);

        await waitFor(() => expect(screen.getByRole('button', { name: /Delete/ })).toBeInTheDocument());
        await userEvent.click(screen.getByRole('button', { name: /Delete/ }));

        await waitFor(() => expect(mockAxiosInstance.delete).toHaveBeenCalledWith('api/manual_transaction/txn-1'));
        expect(screen.getByText('Review List')).toBeInTheDocument();
        expect(screen.getByTestId('location')).toHaveTextContent('/');
    });

    it('falls back to the event detail URL when opened directly with an event return target', async () => {
        const returnTo = '/events/event-1?month=January&category=Dining';
        renderLineItemDetail(`/line_items/line-1?returnTo=${encodeURIComponent(returnTo)}`);

        await waitFor(() => expect(screen.getByRole('button', { name: /Event/ })).toBeInTheDocument());
        await userEvent.click(screen.getByRole('button', { name: /Event/ }));

        expect(screen.getByText('Event Detail')).toBeInTheDocument();
        expect(screen.getByTestId('location')).toHaveTextContent(returnTo);
    });
});
