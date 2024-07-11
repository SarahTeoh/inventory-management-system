import { useEffect, useState } from "react";
import { DeleteItemParams, InventoryTableData, PostItemParams } from "./types"
import { DataTable } from "./data-table"
import axios from "axios";
import { Toaster } from "./ui/toaster";
import { toast } from "./ui/use-toast";
import { ColumnDef } from "@tanstack/react-table";
import { ConfirmDeleteDialog } from "./confirm-delete-dialog";

export default function MainPage() {
    const [inventories, setInventories] = useState([]);
    const [currentCategory, setCurrentCategory] = useState("All");

    function onCategoryChange(newValue: string) {
        setCurrentCategory(newValue)
        const requestParams = newValue.toLowerCase() === "all" ? {} : { filters: { category: newValue } };
        fetchData(requestParams);
    }

    function fetchData(params = {}): void {
        const defaultSort = { field: "last_updated_dt", order: "desc" };
        const requestData = {
            sort: defaultSort,
            ...params,
        };

        axios.post(`https://fs2hjjfa0d.execute-api.ap-southeast-1.amazonaws.com/inventories`, requestData)
            .then(res => {
                setInventories(res.data);
            }).catch(err => {
                console.log(err);
                toast({
                    title: "Unable to fetch data",
                    description: err,
                })
            })
    }

    function postItem(data: PostItemParams): void {
        axios.post(`https://fs2hjjfa0d.execute-api.ap-southeast-1.amazonaws.com/inventory`, data)
            .then(() => {
                toast({
                    description: "Item was created/updated successfully",
                    duration: 3000
                })
                fetchData();
            }).catch(err => {
                console.log(err);
                toast({
                    title: "Something went wrong",
                    description: err,
                    duration: 3000
                })
            })
    }

    function deleteItem(data: DeleteItemParams): void {
        axios.post(`https://fs2hjjfa0d.execute-api.ap-southeast-1.amazonaws.com/inventory/delete`, data)
            .then(() => {
                toast({
                    description: "Item was deleted successfully!",
                    duration: 3000
                })
                fetchData();
            }).catch(err => {
                console.log(err);
                toast({
                    title: "Something went wrong",
                    description: err,
                    duration: 3000
                })
            })
    }

    const columns: ColumnDef<InventoryTableData>[] = [
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
        {
            accessorKey: "Delete",
            cell: ({ row }) => {
                return (
                    <ConfirmDeleteDialog name={row.original.name} category={row.original.category} deleteItem={deleteItem} />
                )
            }
        },
    ]

    useEffect(() => {
        fetchData()
    }, []);

    return (
        <div className="h-full flex-1 flex-col space-y-8 p-1 sm:p-8 md:flex">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-2xl font-bold tracking-tight">Inventory Management System</h2>
            </div>

            <DataTable
                data={inventories}
                columns={columns}
                currentCategory={currentCategory}
                onCategoryChange={onCategoryChange}
                postItem={postItem}
            />
            <Toaster />
        </div>
    )
}
