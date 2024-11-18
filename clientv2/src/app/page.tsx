import { redirect } from 'next/navigation'
import { createClient } from '@/utils/supabase/server'
import { SignOut } from '@/components/SignOut'

export default async function PrivatePage() {
    const supabase = createClient()

    const { data, error: authError } = await supabase.auth.getUser()
    if (authError || !data?.user) {
        console.log('error', authError)
        redirect('/login')
    }

    return (
        <div>
            <h1>Private Page</h1>
            <p>Hello {data.user.email}</p>
            <SignOut />
        </div>
    )
}