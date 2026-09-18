import { useState } from "react";
import type { Order } from "@/types";
import { cancelOrder } from "@/hooks/useOrders";

export function CancelOrderModal({ order, onClose }: { order: Order; onClose: () => void }) {
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleConfirm() {
    setSubmitting(true);
    try {
      await cancelOrder(order.id, reason.trim() || "No reason given");
      onClose();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
        <h2 className="mb-1 font-display text-lg font-bold text-red-600">Cancel Order</h2>
        <p className="mb-4 text-sm text-gray-500">{order.customerName}&apos;s order</p>
        <label className="mb-1 block text-sm font-medium text-gray-700">Reason</label>
        <input
          autoFocus
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="e.g. customer cancelled"
          className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base focus:border-red-400 focus:outline-none"
        />
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-300 py-2.5 font-semibold text-gray-600 hover:bg-gray-50"
          >
            Back
          </button>
          <button
            onClick={handleConfirm}
            disabled={submitting}
            className="flex-1 rounded-lg bg-red-600 py-2.5 font-semibold text-white hover:bg-red-700 disabled:opacity-50"
          >
            {submitting ? "Cancelling…" : "Confirm Cancel"}
          </button>
        </div>
      </div>
    </div>
  );
}
