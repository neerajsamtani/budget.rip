import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Database } from "@/lib/types";
import { currencyFormatter } from "@/lib/utils";
import { PlusIcon } from "lucide-react";

export default function CreateEvent({ selectedRows }: { selectedRows: Database['public']['Tables']['line_items']['Row'][] }) {

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button
                    size="sm"
                    className="ml-auto hidden h-8 lg:flex"
                >
                    <PlusIcon className="h-4 w-4" />
                    Create Event
                </Button>
            </SheetTrigger>
            <SheetContent>
                <SheetHeader>
                    <SheetTitle>Create Event</SheetTitle>
                    <SheetDescription>
                        Create a new event and add selected items to it.
                    </SheetDescription>
                </SheetHeader>
                <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                        <label htmlFor="name" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                            Event Name
                        </label>
                        <Input id="name" placeholder="Enter event name" />
                    </div>
                    <div className="space-y-2">
                        <label htmlFor="description" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                            Description
                        </label>
                        <Input id="description" placeholder="Enter event description" />
                    </div>
                    <div className="space-y-2">
                        <label htmlFor="date" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                            Date
                        </label>
                        <Input id="date" type="date" />
                    </div>
                    {selectedRows.length > 0 && (
                        <div className="rounded-lg border p-3">
                            <h4 className="mb-2 text-sm font-medium">Selected Items</h4>
                            <div className="space-y-2">
                                {selectedRows.map((row) => (
                                    <div key={row.id} className="flex justify-between text-sm">
                                        <span>{row.description}</span>
                                        <span className="font-medium">{currencyFormatter.format(row.amount || 0)}</span>
                                    </div>
                                ))}
                                <div className="flex justify-between text-sm pt-2 border-t">
                                    <span className="font-medium">Total</span>
                                    <span className="font-medium">
                                        {currencyFormatter.format(
                                            selectedRows.reduce((sum, row) =>
                                                sum + (row.amount || 0), 0
                                            )
                                        )}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                <SheetFooter>
                    <SheetClose asChild>
                        <Button type="submit">Save changes</Button>
                    </SheetClose>
                </SheetFooter>
            </SheetContent>
        </Sheet>
    )
}