import { LoginForm } from "@/components/LoginForm";

export default async function LoginPage() {
    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
            <LoginForm />
        </div>
    );
}