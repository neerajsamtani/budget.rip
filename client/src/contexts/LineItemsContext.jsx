import React, { createContext, useEffect, useReducer } from 'react';
import { useContext } from "react";
import axiosInstance from '../axiosInstance';

export const LineItemsContext = createContext([]);
export const LineItemsDispatchContext = createContext([]);

export function useLineItems() {
    return useContext(LineItemsContext);
}

export function useLineItemsDispatch() {
    return useContext(LineItemsDispatchContext);
}

function lineItemsReducer(lineItems, action) {
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
            throw Error('Unknown action: ' + action.type);
        }
    }
}

export function LineItemsProvider({ children }) {
    const initialLineItems = []
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