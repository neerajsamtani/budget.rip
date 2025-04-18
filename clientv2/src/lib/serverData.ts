import { SupabaseClient } from '@supabase/supabase-js';
import moment from 'moment';

export const getLineItemsToReview = async (supabaseClient: SupabaseClient) => {
    const { data: line_items, error } = await supabaseClient
        .from('line_items_to_review')
        .select('date,amount,description,responsible_party,payment_method,id')
        .order('date', { ascending: false })
    if (error) {
        console.error("Error fetching line items:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return line_items;
};

export const getNetEarningsPerMonth = async (supabaseClient: SupabaseClient, startDate?: string, endDate?: string) => {
    const utcStartDate = startDate ? moment(startDate).utc().format('YYYY-MM-DD') : moment(0).utc().format('YYYY-MM-DD');
    const utcEndDate = endDate ? moment(endDate).utc().format('YYYY-MM-DD') : moment().utc().format('YYYY-MM-DD');

    const { data, error } = await supabaseClient
        .from('net_earnings_per_month')
        .select('*')
        .gte('month', utcStartDate)
        .lte('month', utcEndDate)
    if (error) {
        console.error("Error fetching NetEarningsPerMonth:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return data;
};

export const getAmountPerCategoryPerMonth = async (supabaseClient: SupabaseClient, startDate?: string, endDate?: string) => {
    const utcStartDate = startDate ? moment(startDate).utc().format('YYYY-MM-DD') : moment(0).utc().format('YYYY-MM-DD');
    const utcEndDate = endDate ? moment(endDate).utc().format('YYYY-MM-DD') : moment().utc().format('YYYY-MM-DD');

    const { data, error } = await supabaseClient
        .from('amount_per_category_per_month')
        .select('*')
        .gte('month', utcStartDate)
        .lte('month', utcEndDate)
        .order('month', { ascending: true })
    if (error) {
        console.error("Error fetching AmountPerCategoryPerMonth:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return data;
};

export const getActiveAccounts = async (supabaseClient: SupabaseClient) => {
    const { data, error } = await supabaseClient.from('accounts').select('*').order('institution_name', { ascending: true }).eq('status', 'active')
    if (error) {
        console.error("Error fetching Accounts:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return data;
};

export const getStripeInferredBalances = async (supabaseClient: SupabaseClient) => {
    const { data, error } = await supabaseClient.from('latest_stripe_inferred_balances').select('*')
    if (error) {
        console.error("Error fetching StripeInferredBalances:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return data;
};
export const getEvents = async (supabaseClient: SupabaseClient) => {
    const { data, error } = await supabaseClient.from('events').select('*').order('date', { ascending: false })
    if (error) {
        console.error("Error fetching Events:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return data;
};