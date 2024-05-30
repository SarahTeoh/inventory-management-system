import { useEffect, useState } from "react";
import { PostItemParams, columns } from "./types"
import { DataTable } from "./data-table"
import axios from "axios";
import { Toaster } from "./ui/toaster";
import { toast } from "./ui/use-toast";

export default function MainPage() {
    const [inventories, setInventories] = useState([]);
    const [currentCategory, setCurrentCategory] = useState("All");

    function onCategoryChange(newValue: string) {
        setCurrentCategory(newValue)
        fetchData({
            "filters": { "category": newValue }
        });
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
                    description: "Item was created/ updated successfully",
                    duration: 3000
                })
                fetchData(data);
            }).catch(err => {
                console.log(err);
                toast({
                    title: "Something went wrong",
                    description: err,
                    duration: 3000
                })
            })
    }

    useEffect(() => {
        fetchData()
    }, []);

    return (
        <div className="hidden h-full flex-1 flex-col space-y-8 p-8 md:flex">
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
