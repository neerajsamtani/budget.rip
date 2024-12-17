"use client"

import { useRouter } from 'next/navigation'
import { createClient } from '@/utils/supabase/client'

export function SignOut() {
    const supabase = createClient()
    const router = useRouter()
    async function signOut() {
        const { error } = await supabase.auth.signOut()
        if (error) {
            console.log('signOut error', error)
        } else {
            router.push('/login')
        }
    }

    return (
        <button onClick={signOut}>Sign out</button>
    )
}