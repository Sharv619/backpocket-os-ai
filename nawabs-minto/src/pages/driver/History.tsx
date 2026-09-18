import { useMemo } from "react";
import { useDriverAuth } from "@/hooks/useDriverAuth";
import { useOrders } from "@/hooks/useOrders";
import { formatCurrency } from "@/lib/format";

function isToday(ms: number | null): boolean {
  if (!ms) return false;
  const d = new Date(ms);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export function DriverHistory() {
  const { driver } = useDriverAuth();
  const { orders } = useOrders({ driverId: driver?.id });

  const todaysDeliveries = useMemo(
    () => orders.filter((o) => o.status === "delivered" && isToday(o.deliveredAt)),
    [orders],
  );

  return (
    <div className="p-4">
      <h1 className="mb-4 text-lg font-bold text-nawab-maroon-700">Today&apos;s Deliveries</h1>
      {todaysDeliveries.length === 0 ? (
        <p className="text-sm text-gray-400">No completed deliveries yet today.</p>
      ) : (
        <ul className="space-y-2">
          {todaysDeliveries.map((o) => (
            <li key={o.id} className="rounded-xl bg-white p-3 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-800">{o.customerName}</span>
                <span className="text-sm text-gray-500">{formatCurrency(o.totalAmount)}</span>
              </div>
              <p className="text-xs text-gray-400">
                Delivered {o.deliveredAt ? new Date(o.deliveredAt).toLocaleTimeString("en-AU") : ""}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
