'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

import { createClient } from '@/utils/supabase/server'

export async function signup({ first_name, last_name, email, password }: { first_name: string, last_name: string, email: string, password: string }) {
    const supabase = createClient()

    const data = {
        first_name,
        last_name,
        email,
        password,
    }

    const { error } = await supabase.auth.signUp(data)

    if (error) {
        redirect('/error')
    }

    revalidatePath('/', 'layout')
    redirect('/')
}