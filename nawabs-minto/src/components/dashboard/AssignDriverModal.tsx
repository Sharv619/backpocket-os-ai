import { useState } from "react";
import type { Driver, Order } from "@/types";
import { assignDriver, updateOrderStatus } from "@/hooks/useOrders";

interface Props {
  order: Order;
  onlineDrivers: Driver[];
  onClose: () => void;
}

export function AssignDriverModal({ order, onlineDrivers, onClose }: Props) {
  const [driverId, setDriverId] = useState(order.assignedDriverId ?? "");
  const [submitting, setSubmitting] = useState(false);

  async function handleAssign() {
    if (!driverId) return;
    setSubmitting(true);
    try {
      await assignDriver(order.id, driverId);
      await updateOrderStatus(order.id, "out_for_delivery");
      onClose();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
        <h2 className="mb-1 font-display text-lg font-bold text-nawab-maroon-600">
          Assign a Driver
        </h2>
        <p className="mb-4 text-sm text-gray-500">
          {order.customerName} — {order.deliveryAddress}
        </p>

        {onlineDrivers.length === 0 ? (
          <p className="mb-4 rounded-lg bg-orange-50 p-3 text-sm text-orange-700">
            No drivers are online right now. Ask a driver to go online, or hold this order at
            &quot;Ready&quot;.
          </p>
        ) : (
          <div className="mb-4 space-y-2">
            {onlineDrivers.map((d) => (
              <label
                key={d.id}
                className={`flex cursor-pointer items-center justify-between rounded-lg border px-3 py-2.5 text-sm ${
                  driverId === d.id
                    ? "border-nawab-maroon-600 bg-nawab-maroon-50"
                    : "border-gray-300"
                }`}
              >
                <span className="font-medium text-gray-800">{d.name}</span>
                <input
                  type="radio"
                  name="driver"
                  checked={driverId === d.id}
                  onChange={() => setDriverId(d.id)}
                />
              </label>
            ))}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-300 py-2.5 font-semibold text-gray-600 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleAssign}
            disabled={!driverId || submitting}
            className="flex-1 rounded-lg bg-nawab-maroon-600 py-2.5 font-semibold text-white hover:bg-nawab-maroon-700 disabled:opacity-50"
          >
            {submitting ? "Assigning…" : "Assign & Send Out"}
          </button>
        </div>
      </div>
    </div>
  );
}
