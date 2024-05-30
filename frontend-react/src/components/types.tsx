import { ColumnDef } from "@tanstack/react-table"

export enum CategoryEnum {
    MUSIC = "Music",
    GROCERY = "Grocery",
    CLOTHING = "Clothing",
    HOME = "Home",
    BOOKS = "Books",
    OUTDOORS = "Outdoors",
    ELECTRICS = "Electrics",
    BEAUTY = "Beauty"
}
export type CategoryEnumValues = `${CategoryEnum}`;
export type CategoryEnumType = Record<CategoryEnum, string>;
export type PostItemParams = {
    name: string;
    category: CategoryEnumValues;
    price: number;
}

export type Inventory = {
    id: string
    name: string
    category: "Music" | "Grocery" | "Clothing" | "Home" | "Books" | "Outdoors" | "Electrics" | "Beauty"
    price: number
}

export type InventoryTableData = {
    name: string
    category: "Music" | "Grocery" | "Clothing" | "Home" | "Books" | "Outdoors" | "Electrics" | "Beauty"
    price: number
}

export const columns: ColumnDef<InventoryTableData>[] = [
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        accessorKey: "category",
        header: "Category",
    },
    {
        accessorKey: "price",
        header: "Price",
    },
]
