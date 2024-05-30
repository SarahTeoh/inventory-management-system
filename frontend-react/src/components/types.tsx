export enum CategoryEnum {
    ALL = "All",
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
export type DeleteItemParams = {
    name: string;
    category: CategoryEnumValues;
}

export type Inventory = {
    id: string
    name: string
    category: CategoryEnumValues
    price: number
}

export type InventoryTableData = {
    name: string
    category: CategoryEnumValues
    price: number
}

