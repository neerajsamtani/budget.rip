import { Loader2 } from "lucide-react";

export default function Loading() {
    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
            <Loader2 className="h-5 w-5 animate-spin" />
        </div>
    );
}