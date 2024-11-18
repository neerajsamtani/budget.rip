import React, { createContext, ReactNode, useEffect, useReducer } from 'react';
import { useContext } from "react";
import { axiosInstance } from '@/lib/utils';
import { LineItemInterface } from '@/lib/types';

type Action =
    | { type: 'populate_line_items'; fetchedLineItems: LineItemInterface[] }
    | { type: 'toggle_line_item_select'; lineItemId: string }
    | { type: 'remove_line_items'; lineItemIds: string[] };

export const LineItemsContext = createContext<LineItemInterface[]>([]);
export const LineItemsDispatchContext = createContext<React.Dispatch<Action>>(() => { });

export function useLineItems() {
    return useContext(LineItemsContext);
}

export function useLineItemsDispatch() {
    return useContext(LineItemsDispatchContext);
}

function lineItemsReducer(lineItems: LineItemInterface[], action: Action) {
    switch (action.type) {
        case "populate_line_items": {
            return action.fetchedLineItems
        }
        case "toggle_line_item_select": {
            return lineItems.map(lineItem => {
                if (lineItem.id === action.lineItemId) {
                    lineItem.isSelected = !lineItem.isSelected
                    return lineItem;
                } else {
                    return lineItem;
                }
            })
        }
        case "remove_line_items": {
            return lineItems.filter(lineItem => !action.lineItemIds.includes(lineItem.id))
        }
        default: {
            // Use `never` to signal an unreachable case
            const _exhaustiveCheck: never = action;
            return _exhaustiveCheck;
        }
    }
}

export function LineItemsProvider({ children }: { children: ReactNode }) {
    const initialLineItems: LineItemInterface[] = []
    const [lineItems, lineItemsDispatch] = useReducer(lineItemsReducer, initialLineItems);

    useEffect(() => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/line_items`, {
            params: {
                "only_line_items_to_review": true,
            }
        })
            .then(response => {
                lineItemsDispatch({
                    type: "populate_line_items",
                    fetchedLineItems: response.data.data
                })
            })
            .catch(error => console.log(error));
    }, [])

    return (
        <LineItemsContext.Provider value={lineItems}>
            <LineItemsDispatchContext.Provider value={lineItemsDispatch}>
                {children}
            </LineItemsDispatchContext.Provider>
        </LineItemsContext.Provider>
    );
}