import { useDriverAuth } from "@/hooks/useDriverAuth";
import { useOrders } from "@/hooks/useOrders";
import { DriverOrderCard } from "@/components/driver/DriverOrderCard";

export function DriverHome() {
  const { driver } = useDriverAuth();
  const { orders, loading } = useOrders({ activeOnly: true, driverId: driver?.id });

  if (loading) {
    return <p className="p-6 text-center text-gray-400">Loading…</p>;
  }

  if (orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
        <p className="text-5xl">📭</p>
        <p className="mt-4 text-lg font-semibold text-gray-600">No deliveries assigned</p>
        <p className="mt-1 text-sm text-gray-400">
          {driver?.status === "online"
            ? "Stay online — the shop will assign your next order."
            : "Go online when you're ready for a delivery."}
        </p>
      </div>
    );
  }

  return (
    <div className="pb-6">
      {orders.map((order) => (
        <DriverOrderCard key={order.id} order={order} />
      ))}
    </div>
  );
}
