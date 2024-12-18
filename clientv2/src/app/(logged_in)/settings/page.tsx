"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { useToast } from "@/components/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { createClient } from "@/utils/supabase/client"
import { UpdateIcon } from "@radix-ui/react-icons"
import { useEffect, useState } from "react"
import { updateProfile } from "./actions"

const profileFormSchema = z.object({
    firstName: z
        .string()
        .min(2, {
            message: "First name must be at least 2 characters.",
        })
        .max(30, {
            message: "First name must not be longer than 30 characters.",
        }),
    lastName: z
        .string()
        .min(2, {
            message: "Last name must be at least 2 characters.",
        })
        .max(30, {
            message: "Last name must not be longer than 30 characters.",
        }),
    email: z
        .string()
        .email("Invalid email address")
        .optional()
})

type ProfileFormValues = z.infer<typeof profileFormSchema>

const defaultValues: Partial<ProfileFormValues> = {
    firstName: "",
    lastName: "",
    email: "",
}

export default function SettingsPage() {
    const supabaseClient = createClient()
    const { toast } = useToast()
    const [isLoading, setIsLoading] = useState(false)

    const form = useForm<ProfileFormValues>({
        resolver: zodResolver(profileFormSchema),
        defaultValues,
        mode: "onTouched",
        delayError: 500,
    })

    useEffect(() => {
        const fetchData = async () => {
            try {
                const userResponse = await supabaseClient.auth.getUser()
                const user = userResponse.data.user
                if (!user) {
                    throw new Error("User not found")
                }

                const { data, error } = await supabaseClient.from('profiles').select('*').eq('id', user.id).single()
                if (error) {
                    throw error
                }
                form.reset({
                    firstName: data.first_name || "",
                    lastName: data.last_name || "",
                    email: data.email || "",
                })
            } catch (err) {
                toast({
                    variant: "destructive",
                    title: "Error fetching data",
                    description: err instanceof Error ? err.message : "Unknown error",
                })
            }
        }

        fetchData()
    }, [supabaseClient, form])

    async function onSubmit(data: ProfileFormValues) {
        setIsLoading(true)
        const result = await updateProfile({
            firstName: data.firstName,
            lastName: data.lastName,
        })
        if (result?.error) {
            toast({
                variant: "destructive",
                title: "Error",
                description: result.error,
            })
        }
        if (result?.data) {
            toast({
                title: "Profile updated",
                description: "Your profile has been updated successfully",
            })
        }
        setIsLoading(false)
    }

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
            <Card className="w-full max-w-sm">
                <CardHeader>
                    <CardTitle className="text-2xl">Profile</CardTitle>
                    <CardDescription>
                        Update your profile information.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                            <FormField
                                control={form.control}
                                name="firstName"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>First Name</FormLabel>
                                        <FormControl>
                                            <Input {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="lastName"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Last Name</FormLabel>
                                        <FormControl>
                                            <Input {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="email"
                                disabled={true}
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Email</FormLabel>
                                        <FormControl>
                                            <Input type="email" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <div className="w-full">
                                {
                                    isLoading ?
                                        <Button disabled className="w-full">
                                            <UpdateIcon className="mr-2 h-4 w-4 animate-spin" />
                                            Please wait
                                        </Button>
                                        :
                                        <Button className="w-full" type="submit">Update profile</Button>
                                }
                            </div>
                        </form>
                    </Form>
                </CardContent>
            </Card>
        </div>
    )
}
