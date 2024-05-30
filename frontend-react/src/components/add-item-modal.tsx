
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "./ui/input";
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { useForm } from "react-hook-form";
import { CategoryEnum } from "./types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { PostItemParams } from "./types"
import { useState } from "react";

export default function AddItemModal({ categories, postItem }: { categories: CategoryEnum[], postItem: (params: PostItemParams) => void }) {
    const [open, setOpen] = useState(false)
    const formSchema = z.object({
        name: z.string({
            required_error: "Please insert item name.",
        }).min(2),
        category: z.nativeEnum(CategoryEnum, {
            required_error: "Please select item's category",
        }),
        price: z.coerce.number({
            required_error: "Please insert item price.",
        }).gt(0.1, { message: "Please insert price greater than 0.1" }).positive({ message: "Please enter value greater than zero" }),
    })

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            category: CategoryEnum.BEAUTY,
            price: 0.0
        },
    })

    function onSubmit(values: z.infer<typeof formSchema>) {
        setOpen(false)
        postItem(values);
    }

    return (<>
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline">Add item</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Add item</DialogTitle>
                    <DialogDescription>
                        Add new item here. If item already exists, item will be updated with new Price. Click 'Save Item' when you're finished.
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                        <div className="grid gap-4 py-4">
                            {/* name */}
                            <FormField
                                control={form.control}
                                name="name"
                                render={({ field }) => (
                                    <FormItem>
                                        <div className="grid grid-cols-4 items-center gap-x-4 gap-y-2">
                                            <FormLabel htmlFor="price" className="text-right">
                                                Name
                                            </FormLabel>
                                            <FormControl>
                                                <Input id="name" {...field} placeholder="name" className="col-span-3" />
                                            </FormControl>
                                            <FormMessage className="col-start-2 col-span-3" />
                                        </div>
                                    </FormItem>
                                )}
                            />
                            {/* category */}
                            <FormField
                                control={form.control}
                                name="category"
                                render={({ field }) => (
                                    <FormItem>
                                        <div className="grid grid-cols-4 items-center gap-x-4 gap-y-2">
                                            <FormLabel className="text-right">
                                                Category
                                            </FormLabel>
                                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                                                <FormControl className="col-span-3" >
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Select item category" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    {categories.map((category: string) => {
                                                        return (<SelectItem key={category} value={category}>{category}</SelectItem>
                                                        )
                                                    })
                                                    }
                                                </SelectContent>
                                            </Select>
                                            <FormMessage className="col-start-2 col-span-3" />
                                        </div>
                                    </FormItem>
                                )}
                            />

                            {/* Price */}
                            <FormField
                                control={form.control}
                                name="price"
                                render={({ field }) => (
                                    <FormItem>
                                        <div className="grid grid-cols-4 items-center gap-x-4 gap-y-2">
                                            <FormLabel htmlFor="price" className="text-right">
                                                Price
                                            </FormLabel>
                                            <FormControl>
                                                <Input id="price" {...field} min="0" className="col-span-3" />
                                            </FormControl>
                                            <FormMessage className="col-start-2 col-span-3" />
                                        </div>
                                    </FormItem>
                                )}
                            />
                        </div>
                        <DialogFooter>
                            <Button type="submit">Save Item</Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent >
        </Dialog >
    </>
    )
}