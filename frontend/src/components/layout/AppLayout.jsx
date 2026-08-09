import { Outlet } from "react-router-dom";

import AppSidebar from "./AppSidebar";
import AppNavbar from "./AppNavbar";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen bg-slate-950 text-white">
      <AppSidebar />

      <div className="flex flex-1 flex-col">
        <AppNavbar />

        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}