import { axiosInstance } from "./utils";

import { createClient } from '@/utils/supabase/server'

export const getLineItems = async (
    params: {
        payment_method?: string;
        month?: string;
        year?: string;
    } = {}
) => {
    try {
        // TODO: Get the REACT_APP_API_ENDPOINT in the process environment variable
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        REACT_APP_API_ENDPOINT = "http://dev.localhost:4242/";
        const { data } = await axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/line_items`, {
            params,
        });
        return data.data;
    } catch (error) {
        console.error("Error fetching line items:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
};

export const getPaymentMethods = async () => {
    try {
        // TODO: Get the REACT_APP_API_ENDPOINT in the process environment variable
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        REACT_APP_API_ENDPOINT = "http://dev.localhost:4242/";
        const { data } = await axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/payment_methods`);
        return data;
    } catch (error) {
        console.error("Error fetching payment methods:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
};

export const getLineItemsToReviewSupabase = async () => {
    const supabase = createClient()
    const { data: line_items, error } = await supabase
        .from('line_items')
        .select('date,amount,description,responsible_party,payment_method,id')
        .order('date', { ascending: false })
        .is('event_id', null)
        .limit(5)
    if (error) {
        console.error("Error fetching line items:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return line_items;
};