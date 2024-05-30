import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import AddItemModal from "./add-item-modal";
import { CategoryEnum, PostItemParams } from "./types";
import { Table } from "@tanstack/react-table";


interface DataTableToolbarProps<TData> {
    table: Table<TData>
    currentCategory: string;
    onCategoryChange: (value: string) => void;
    postItem: (params: PostItemParams) => void;
}

interface SelectCategoryProps {
    categories: CategoryEnum[];
    currentCategory: string;
    onCategoryChange: (value: string) => void;
}

interface TextInputProps<TData> {
    table: Table<TData>
}

function SelectCategory({
    categories, currentCategory, onCategoryChange
}: SelectCategoryProps) {
    return (
        <Select value={currentCategory} onValueChange={(value) => onCategoryChange(value)}>
            <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
                <SelectGroup>
                    <SelectLabel>Category</SelectLabel>
                    {categories.map((category: string) => {
                        return (
                            <SelectItem key={category} value={category}>{category}</SelectItem>
                        )
                    })
                    }
                </SelectGroup>
            </SelectContent>
        </Select>
    )
}

function TextInputProps<TData>({
    table
}: TextInputProps<TData>) {
    // Note: Not fetching data directly from the database to reduce comsumption of DynamoDB RCU
    return (
        <Input
            placeholder="Filter by name"
            value={(table.getColumn("name")?.getFilterValue() as string) ?? ""}
            onChange={(event) => {
                table.getColumn("name")?.setFilterValue(event.target.value)
            }}
            className="h-8 w-[150px] lg:w-[250px]"
        />
    )
}

export function DataTableToolbar<TData>({
    table,
    currentCategory,
    onCategoryChange,
    postItem
}: DataTableToolbarProps<TData>) {
    const categories = Object.values(CategoryEnum);
    return (
        <div className="flex items-center justify-between">
            <div className="flex flex-1 items-center space-x-2">
                <TextInputProps table={table} />
                <SelectCategory categories={categories} currentCategory={currentCategory} onCategoryChange={onCategoryChange} />
            </div>
            <AddItemModal categories={categories} postItem={postItem} />
        </div>
    )
}