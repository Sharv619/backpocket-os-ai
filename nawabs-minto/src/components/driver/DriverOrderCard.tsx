import { useState } from "react";
import type { Order } from "@/types";
import { formatCurrency, navigateHref, telHref } from "@/lib/format";
import { nextStatus, nextStatusLabel } from "@/lib/orderStatus";
import { updateOrderStatus } from "@/hooks/useOrders";
import { IssueModal } from "@/components/driver/IssueModal";

export function DriverOrderCard({ order }: { order: Order }) {
  const [updating, setUpdating] = useState(false);
  const [showIssue, setShowIssue] = useState(false);
  const next = nextStatus(order);

  async function handleAdvance() {
    if (!next) return;
    setUpdating(true);
    try {
      await updateOrderStatus(order.id, next);
    } finally {
      setUpdating(false);
    }
  }

  return (
    <div className="mx-4 mt-4 rounded-2xl bg-white p-5 shadow-md">
      <div className="flex items-start justify-between">
        <h2 className="text-lg font-bold text-gray-900">{order.customerName}</h2>
        <a
          href={telHref(order.customerPhone)}
          className="rounded-full bg-nawab-maroon-50 px-3 py-1.5 text-sm font-semibold text-nawab-maroon-600"
        >
          📞 Call
        </a>
      </div>

      {order.orderType === "delivery" && (
        <p className="mt-2 text-base text-gray-700">{order.deliveryAddress}</p>
      )}

      <div className="mt-3 rounded-lg bg-gray-50 p-3">
        <ul className="space-y-1 text-sm text-gray-700">
          {order.orderItems.map((item, i) => (
            <li key={i}>
              {item.quantity}× {item.name}
              {item.notes && <span className="text-gray-400"> — {item.notes}</span>}
            </li>
          ))}
        </ul>
      </div>

      {order.notes && (
        <p className="mt-2 rounded-lg bg-yellow-50 p-2 text-sm text-yellow-800">
          Note: {order.notes}
        </p>
      )}

      <div className="mt-3 flex items-center justify-between">
        <span className="text-xl font-bold text-gray-900">
          {formatCurrency(order.totalAmount)}
        </span>
        <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold uppercase text-gray-500">
          {order.paymentMethod === "cash" ? "💵 Collect Cash" : "Paid"}
        </span>
      </div>

      {order.orderType === "delivery" && (
        <a
          href={navigateHref(order.deliveryAddress)}
          target="_blank"
          rel="noreferrer"
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-4 text-lg font-bold text-white"
        >
          🧭 Navigate
        </a>
      )}

      {next && (
        <button
          onClick={handleAdvance}
          disabled={updating}
          className="mt-3 w-full rounded-xl bg-nawab-maroon-600 py-4 text-lg font-bold text-white disabled:opacity-60"
        >
          {updating ? "Updating…" : nextStatusLabel(order)}
        </button>
      )}

      <button
        onClick={() => setShowIssue(true)}
        className="mt-3 w-full rounded-xl border border-red-300 py-3 text-sm font-semibold text-red-600"
      >
        ⚠ Flag an Issue
      </button>

      {order.issue && !order.issue.resolved && (
        <p className="mt-2 text-xs text-red-500">
          Issue reported: {order.issue.note} — waiting on shop
        </p>
      )}

      {showIssue && <IssueModal order={order} onClose={() => setShowIssue(false)} />}
    </div>
  );
}
