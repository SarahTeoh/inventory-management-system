import { useEffect } from "react";

export default function MainPage() {
    useEffect(() => {
        // TODO: fetch data from api gateway
    }, []);

    return (
        <div className="hidden h-full flex-1 flex-col space-y-8 p-8 md:flex">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-2xl font-bold tracking-tight">Inventory Management System</h2>
            </div>
        </div>
    )
}
