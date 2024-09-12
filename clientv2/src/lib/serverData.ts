import { createClient } from '@/utils/supabase/server'

export const getLineItemsToReview = async () => {
    const supabase = createClient()
    const { data: line_items, error } = await supabase
        .from('line_items_to_review')
        .select('date,amount,description,responsible_party,payment_method,id')
    if (error) {
        console.error("Error fetching line items:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return line_items;
};

export const getNetEarningsPerMonth = async () => {
    const supabase = createClient()
    const { data, error } = await supabase
        .from('net_earnings_per_month')
        .select('*')
    if (error) {
        console.error("Error fetching NetEarningsPerMonth:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return data;
};

export const getAmountPerCategoryPerMonth = async () => {
    const supabase = createClient()
    const { data, error } = await supabase
        .from('amount_per_category_per_month')
        .select('*')
    if (error) {
        console.error("Error fetching AmountPerCategoryPerMonth:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
    return data;
};