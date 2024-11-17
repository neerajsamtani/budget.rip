import { createClient } from '@/utils/supabase/server'
import { redirect } from 'next/navigation'

export default async function RootPage() {
    const supabase = createClient()

    const { data, error: authError } = await supabase.auth.getUser()
    if (authError || !data?.user) {
        console.log('error', authError)
        redirect('/login')
    }

    redirect('/dashboard')
}