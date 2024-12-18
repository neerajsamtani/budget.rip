'use server'

import { createClient } from '@/utils/supabase/server'

export async function updateProfile({ firstName, lastName }: { firstName: string, lastName: string }) {
    const supabase = createClient()
    const userResponse = await supabase.auth.getUser()
    const user = userResponse.data.user
    if (!user) {
        return { error: "User not found" }
    }

    const { error, data } = await supabase.from('profiles').update({
        first_name: firstName,
        last_name: lastName,
    }).eq('id', user.id)
        .select()

    if (error) {
        return { error: error.message }
    }

    return { data }
}