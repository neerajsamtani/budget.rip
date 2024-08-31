import { redirect } from 'next/navigation'
import { createClient } from '@/utils/supabase/server'
import { SignOut } from '@/components/SignOut'

export default async function PrivatePage() {
    const supabase = createClient()

    const { data, error } = await supabase.auth.getUser()
    if (error || !data?.user) {
        console.log('error', error)
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