import { useEffect, useState } from "react";
import type { Driver, Order } from "@/types";
import { nextStatus, nextStatusLabel, timeSinceLabel, urgencyLevel, URGENCY_CARD_CLASSES } from "@/lib/orderStatus";
import { formatCurrency, telHref } from "@/lib/format";
import { updateOrderStatus } from "@/hooks/useOrders";

interface Props {
  order: Order;
  drivers: Driver[];
  onRequestAssign: () => void;
  onEdit: () => void;
  onCancel: () => void;
}

export function OrderCard({ order, drivers, onRequestAssign, onEdit, onCancel }: Props) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30_000);
    return () => clearInterval(id);
  }, []);

  const urgency = urgencyLevel(order, now);
  const next = nextStatus(order);
  const driver = drivers.find((d) => d.id === order.assignedDriverId);
  const canEdit = order.status === "new" || order.status === "preparing";

  async function handleAdvance() {
    if (!next) return;
    if (order.status === "ready" && order.orderType === "delivery" && !order.assignedDriverId) {
      onRequestAssign();
      return;
    }
    await updateOrderStatus(order.id, next);
  }

  return (
    <div className={`rounded-xl p-4 shadow-sm ${URGENCY_CARD_CLASSES[urgency]}`}>
      <div className="mb-1 flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900">{order.customerName}</h3>
        <span className="text-lg" title={order.orderType}>
          {order.orderType === "pickup" ? "🏬" : "🚗"}
        </span>
      </div>

      <a href={telHref(order.customerPhone)} className="text-sm text-nawab-maroon-600 underline">
        {order.customerPhone}
      </a>

      <p className="mt-2 line-clamp-2 text-sm text-gray-600">
        {order.orderItems.map((it) => `${it.quantity}× ${it.name}`).join(", ")}
      </p>

      {order.issue && !order.issue.resolved && (
        <p className="mt-2 rounded bg-red-100 px-2 py-1 text-xs font-semibold text-red-700">
          ⚠ Driver flagged: {order.issue.note}
        </p>
      )}

      <div className="mt-2 flex items-center justify-between text-sm">
        <span className="font-semibold text-gray-900">{formatCurrency(order.totalAmount)}</span>
        <span className="text-gray-400">{timeSinceLabel(order.createdAt, now)}</span>
      </div>

      {driver && (
        <p className="mt-1 text-xs text-gray-500">
          Driver: <span className="font-medium">{driver.name}</span>
        </p>
      )}

      <div className="mt-3 flex gap-2">
        {canEdit && (
          <button
            onClick={onEdit}
            className="rounded-lg border border-gray-300 px-3 py-2 text-xs font-semibold text-gray-500 hover:bg-gray-50"
          >
            Edit
          </button>
        )}
        <button
          onClick={onCancel}
          className="rounded-lg border border-gray-300 px-3 py-2 text-xs font-semibold text-gray-500 hover:bg-red-50 hover:text-red-600"
        >
          Cancel
        </button>
        {next && (
          <button
            onClick={handleAdvance}
            className="ml-auto flex-1 rounded-lg bg-nawab-maroon-600 px-3 py-2 text-xs font-semibold text-white hover:bg-nawab-maroon-700"
          >
            {nextStatusLabel(order)} →
          </button>
        )}
      </div>
    </div>
  );
}
