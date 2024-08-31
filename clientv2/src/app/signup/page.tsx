"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { UpdateIcon } from "@radix-ui/react-icons"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { set, useForm } from "react-hook-form"
import { signup } from './actions'
import { useState } from "react"

const formSchema = z.object({
    first_name: z.string().min(1, {
        message: "First name cannot be blank",
    }),
    last_name: z.string().min(1, {
        message: "Last name cannot be blank",
    }),
    email: z.string().email({
        message: "Please enter a valid email address",
    }),
    password: z.string().min(8, {
        message: "Password must be at least 8 characters long",
    })
})

export default function SignupPage() {
    const [isLoading, setIsLoading] = useState(false)
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            first_name: "",
            last_name: "",
            email: "",
            password: "",
        },
    })
    async function onSubmit(values: z.infer<typeof formSchema>) {
        setIsLoading(true)
        await signup(values)
        setIsLoading(false)
    }
    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
            <Card className="w-full max-w-sm">
                <CardHeader>
                    <CardTitle className="text-2xl">Sign Up</CardTitle>
                    <CardDescription>
                        Enter your information to create an account
                    </CardDescription>
                </CardHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                        <CardContent className="grid gap-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="grid gap-2">
                                    <FormField
                                        control={form.control}
                                        name="first_name"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>First name</FormLabel>
                                                <FormControl>
                                                    <Input id="first_name" type="text" required placeholder="John" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <FormField
                                        control={form.control}
                                        name="last_name"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Last name</FormLabel>
                                                <FormControl>
                                                    <Input id="last_name" type="text" required placeholder="Doe" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>
                            </div>
                            <div className="grid gap-2">
                                <FormField
                                    control={form.control}
                                    name="email"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Email</FormLabel>
                                            <FormControl>
                                                <Input id="email" type="email" required placeholder="john@example.com" {...field} />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>
                            <div className="grid gap-2">
                                <FormField
                                    control={form.control}
                                    name="password"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Password</FormLabel>
                                            <FormControl>
                                                <Input id="password" type="password" required {...field} />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>
                            <div className="w-full">
                                {
                                    isLoading ?
                                        <Button disabled className="w-full">
                                            <UpdateIcon className="mr-2 h-4 w-4 animate-spin" />
                                            Please wait
                                        </Button>
                                        :
                                        <Button className="w-full" type="submit">Sign Up</Button>
                                }
                            </div>
                            <div className="text-center text-sm">
                                Already have an account?{" "}
                                <Link href="/login" className="underline">
                                    Log In
                                </Link>
                            </div>
                        </CardContent>
                    </form>
                </Form>
            </Card>
        </div>
    );
}