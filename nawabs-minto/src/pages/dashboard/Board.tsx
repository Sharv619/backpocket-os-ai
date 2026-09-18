import { useMemo, useState } from "react";
import { useOrders } from "@/hooks/useOrders";
import { useDrivers } from "@/hooks/useDrivers";
import { useDashboardAlerts } from "@/hooks/useDashboardAlerts";
import { OrderCard } from "@/components/dashboard/OrderCard";
import { NewOrderModal } from "@/components/dashboard/NewOrderModal";
import { AssignDriverModal } from "@/components/dashboard/AssignDriverModal";
import { CancelOrderModal } from "@/components/dashboard/CancelOrderModal";
import { ToastStack } from "@/components/dashboard/ToastStack";
import type { Order, OrderStatus } from "@/types";
import { ORDER_STATUS_LABELS } from "@/types";

const BOARD_COLUMNS: OrderStatus[] = ["new", "preparing", "ready", "out_for_delivery", "delivered"];

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

export function DashboardBoard() {
  const { orders } = useOrders();
  const { drivers } = useDrivers();
  const { toasts, dismiss } = useDashboardAlerts(orders);

  const [showNewOrder, setShowNewOrder] = useState(false);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [assigningOrder, setAssigningOrder] = useState<Order | null>(null);
  const [cancellingOrder, setCancellingOrder] = useState<Order | null>(null);

  const onlineDrivers = useMemo(() => drivers.filter((d) => d.status === "online"), [drivers]);

  const columns = useMemo(() => {
    const map: Record<OrderStatus, Order[]> = {
      new: [],
      preparing: [],
      ready: [],
      out_for_delivery: [],
      delivered: [],
      cancelled: [],
    };
    for (const order of orders) {
      if (order.status === "cancelled") continue;
      if (order.status === "delivered" && !isToday(order.deliveredAt)) continue;
      map[order.status].push(order);
    }
    return map;
  }, [orders]);

  function handleAdvanceRequiresAssign(order: Order) {
    setAssigningOrder(order);
  }

  return (
    <div className="p-4 sm:p-6">
      <ToastStack toasts={toasts} onDismiss={dismiss} />

      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold text-nawab-maroon-700">Order Queue</h1>
        <button
          onClick={() => setShowNewOrder(true)}
          className="rounded-xl bg-nawab-maroon-600 px-5 py-3 text-base font-bold text-white shadow-md hover:bg-nawab-maroon-700"
        >
          + New Order
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {BOARD_COLUMNS.map((status) => (
          <div key={status} className="rounded-2xl bg-nawab-gold-100/40 p-3">
            <div className="mb-3 flex items-center justify-between px-1">
              <h2 className="text-sm font-bold uppercase tracking-wide text-nawab-maroon-700">
                {ORDER_STATUS_LABELS[status]}
              </h2>
              <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-gray-500">
                {columns[status].length}
              </span>
            </div>
            <div className="flex flex-col gap-3">
              {columns[status].length === 0 && (
                <p className="px-1 text-xs text-gray-400">No orders</p>
              )}
              {columns[status].map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  drivers={drivers}
                  onRequestAssign={() => handleAdvanceRequiresAssign(order)}
                  onEdit={() => setEditingOrder(order)}
                  onCancel={() => setCancellingOrder(order)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {(showNewOrder || editingOrder) && (
        <NewOrderModal
          editingOrder={editingOrder}
          onClose={() => {
            setShowNewOrder(false);
            setEditingOrder(null);
          }}
        />
      )}
      {assigningOrder && (
        <AssignDriverModal
          order={assigningOrder}
          onlineDrivers={onlineDrivers}
          onClose={() => setAssigningOrder(null)}
        />
      )}
      {cancellingOrder && (
        <CancelOrderModal order={cancellingOrder} onClose={() => setCancellingOrder(null)} />
      )}
    </div>
  );
}
