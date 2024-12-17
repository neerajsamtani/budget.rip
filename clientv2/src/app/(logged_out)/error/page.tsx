import { Button } from "@/components/ui/button"
import Link from 'next/link'

export default function ErrorPage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-12">
            <p>Sorry, something went wrong.</p>
            <p>Please try again later or contact support.</p>
            <Button asChild className="mt-5">
                <Link href="/">
                    Go Home
                </Link>
            </Button>
        </div>
    )
}       