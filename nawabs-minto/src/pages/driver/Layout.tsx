import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useDriverAuth } from "@/hooks/useDriverAuth";
import { useOrders } from "@/hooks/useOrders";
import { setDriverStatus } from "@/hooks/useDrivers";
import { useRegisterFcmToken } from "@/hooks/useRegisterFcmToken";

export function DriverLayout() {
  const { driver, signOut } = useDriverAuth();
  const { orders } = useOrders({ activeOnly: true, driverId: driver?.id });
  const [toggling, setToggling] = useState(false);
  const [warning, setWarning] = useState<string | null>(null);

  useRegisterFcmToken(driver?.id);

  const hasActiveOrder = orders.length > 0;

  async function handleToggle() {
    if (!driver) return;
    setWarning(null);
    if (driver.status === "online" && hasActiveOrder) {
      setWarning("You can't go offline while you have an active delivery.");
      return;
    }
    setToggling(true);
    try {
      await setDriverStatus(driver.id, driver.status === "online" ? "offline" : "online");
    } finally {
      setToggling(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-nawab-cream">
      <header className="bg-white px-4 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-base font-bold text-nawab-maroon-700">
              {driver?.name ?? "Driver"}
            </h1>
          </div>
          <button
            onClick={() => void signOut()}
            className="text-sm font-medium text-gray-400"
          >
            Sign out
          </button>
        </div>
        <button
          onClick={handleToggle}
          disabled={toggling}
          className={`mt-3 flex w-full items-center justify-center gap-2 rounded-xl py-3 text-base font-bold transition disabled:opacity-60 ${
            driver?.status === "online"
              ? "bg-green-500 text-white"
              : "bg-gray-200 text-gray-600"
          }`}
        >
          <span className="h-2.5 w-2.5 rounded-full bg-white/90" />
          {driver?.status === "online" ? "ONLINE — tap to go offline" : "OFFLINE — tap to go online"}
        </button>
        {warning && <p className="mt-2 text-sm font-medium text-red-600">{warning}</p>}
      </header>

      <main className="flex-1 pb-20">
        <Outlet />
      </main>

      <nav className="fixed bottom-0 left-0 right-0 flex border-t border-gray-200 bg-white">
        {[
          { to: "/driver/home", label: "Deliveries" },
          { to: "/driver/history", label: "History" },
        ].map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex-1 py-3 text-center text-sm font-semibold ${
                isActive ? "text-nawab-maroon-600" : "text-gray-400"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
