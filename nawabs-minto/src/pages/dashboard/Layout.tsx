import { NavLink, Outlet } from "react-router-dom";
import { useStaffAuth } from "@/hooks/useStaffAuth";

const NAV_ITEMS = [
  { to: "/dashboard/board", label: "Order Queue" },
  { to: "/dashboard/drivers", label: "Drivers" },
  { to: "/dashboard/history", label: "History" },
];

export function DashboardLayout() {
  const { staff, signOut } = useStaffAuth();

  return (
    <div className="min-h-screen bg-nawab-cream">
      <header className="flex items-center justify-between border-b border-nawab-gold-300/60 bg-white px-4 py-3 sm:px-6">
        <div>
          <h1 className="font-display text-lg font-bold text-nawab-maroon-700">
            Nawab&apos;s Minto
          </h1>
          <p className="text-xs text-gray-400">{staff?.name ?? staff?.email}</p>
        </div>
        <nav className="flex gap-1 rounded-lg bg-nawab-gold-100/60 p-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-sm font-semibold transition ${
                  isActive
                    ? "bg-white text-nawab-maroon-700 shadow-sm"
                    : "text-nawab-maroon-500/70 hover:text-nawab-maroon-700"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={() => void signOut()}
          className="text-sm font-medium text-gray-400 hover:text-nawab-maroon-600"
        >
          Sign out
        </button>
      </header>
      <Outlet />
    </div>
  );
}
