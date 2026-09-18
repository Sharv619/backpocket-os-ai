import { useMemo } from "react";
import { useDrivers } from "@/hooks/useDrivers";
import { useOrders } from "@/hooks/useOrders";

export function DashboardDrivers() {
  const { drivers } = useDrivers();
  const { orders } = useOrders({ activeOnly: true });

  const currentOrderByDriver = useMemo(() => {
    const map = new Map<string, string>();
    for (const order of orders) {
      if (order.assignedDriverId) map.set(order.assignedDriverId, order.customerName);
    }
    return map;
  }, [orders]);

  return (
    <div className="p-4 sm:p-6">
      <h1 className="mb-6 font-display text-2xl font-bold text-nawab-maroon-700">Drivers</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {drivers.map((d) => {
          const currentOrder = currentOrderByDriver.get(d.id);
          return (
            <div key={d.id} className="rounded-xl bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">{d.name}</h3>
                <span
                  className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${
                    d.status === "online"
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${d.status === "online" ? "bg-green-500" : "bg-gray-400"}`}
                  />
                  {d.status === "online" ? "Online" : "Offline"}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-500">{d.phone}</p>
              <p className="mt-3 text-sm">
                {currentOrder ? (
                  <span className="font-medium text-nawab-maroon-600">
                    On delivery: {currentOrder}
                  </span>
                ) : d.status === "online" ? (
                  <span className="text-green-600">Free for next delivery</span>
                ) : (
                  <span className="text-gray-400">Not on shift</span>
                )}
              </p>
            </div>
          );
        })}
        {drivers.length === 0 && (
          <p className="text-sm text-gray-400">
            No drivers set up yet. Add drivers to the <code>drivers</code> collection in
            Firestore.
          </p>
        )}
      </div>
    </div>
  );
}
