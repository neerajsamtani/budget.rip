import { createClient } from '@/utils/supabase/server'

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