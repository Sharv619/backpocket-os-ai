import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import type { Order, OrderItem, OrderType, PaymentMethod } from "@/types";
import { createOrder, editOrder } from "@/hooks/useOrders";
import { useStaffAuth } from "@/hooks/useStaffAuth";

interface Props {
  onClose: () => void;
  editingOrder?: Order | null;
}

function emptyItem(): OrderItem {
  return { name: "", quantity: 1, notes: "" };
}

export function NewOrderModal({ onClose, editingOrder }: Props) {
  const { staff } = useStaffAuth();
  const [customerName, setCustomerName] = useState(editingOrder?.customerName ?? "");
  const [customerPhone, setCustomerPhone] = useState(editingOrder?.customerPhone ?? "");
  const [orderType, setOrderType] = useState<OrderType>(editingOrder?.orderType ?? "delivery");
  const [deliveryAddress, setDeliveryAddress] = useState(editingOrder?.deliveryAddress ?? "");
  const [items, setItems] = useState<OrderItem[]>(
    editingOrder?.orderItems && editingOrder.orderItems.length > 0
      ? editingOrder.orderItems
      : [emptyItem()],
  );
  const [totalAmount, setTotalAmount] = useState(
    editingOrder ? String(editingOrder.totalAmount) : "",
  );
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>(
    editingOrder?.paymentMethod ?? "cash",
  );
  const [notes, setNotes] = useState(editingOrder?.notes ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const itemNameRefs = useRef<(HTMLInputElement | null)[]>([]);

  function updateItem(index: number, patch: Partial<OrderItem>) {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  }

  function addItemRow(focusAfter = true) {
    setItems((prev) => [...prev, emptyItem()]);
    if (focusAfter) {
      requestAnimationFrame(() => {
        itemNameRefs.current[items.length]?.focus();
      });
    }
  }

  function removeItemRow(index: number) {
    setItems((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== index) : prev));
  }

  function handleItemKeyDown(e: KeyboardEvent<HTMLInputElement>, index: number) {
    if (e.key === "Enter") {
      e.preventDefault();
      if (index === items.length - 1) {
        addItemRow();
      } else {
        itemNameRefs.current[index + 1]?.focus();
      }
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const cleanItems = items
      .map((it) => ({ ...it, name: it.name.trim() }))
      .filter((it) => it.name.length > 0);
    if (cleanItems.length === 0) {
      setError("Add at least one order item.");
      return;
    }
    if (orderType === "delivery" && deliveryAddress.trim().length === 0) {
      setError("Delivery address is required for delivery orders.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        customerName: customerName.trim(),
        customerPhone: customerPhone.trim(),
        deliveryAddress: orderType === "pickup" ? "" : deliveryAddress.trim(),
        orderItems: cleanItems,
        totalAmount: Number(totalAmount) || 0,
        orderType,
        paymentMethod,
        notes: notes.trim(),
      };
      if (editingOrder) {
        await editOrder(editingOrder.id, payload);
      } else {
        await createOrder({ ...payload, createdBy: staff?.name ?? staff?.email ?? "staff" });
      }
      onClose();
    } catch {
      setError("Couldn't save the order. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 p-4 pt-8">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-display text-xl font-bold text-nawab-maroon-600">
            {editingOrder ? "Edit Order" : "New Order"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Customer Name</label>
            <input
              autoFocus
              required
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base focus:border-nawab-maroon-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Phone Number</label>
            <input
              required
              type="tel"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base focus:border-nawab-maroon-400 focus:outline-none"
            />
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          {(["delivery", "pickup"] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setOrderType(t)}
              className={`flex-1 rounded-lg border py-2.5 text-sm font-semibold capitalize transition ${
                orderType === t
                  ? "border-nawab-maroon-600 bg-nawab-maroon-50 text-nawab-maroon-700"
                  : "border-gray-300 text-gray-500"
              }`}
            >
              {t === "delivery" ? "🚗 Delivery" : "🏬 Pickup"}
            </button>
          ))}
        </div>

        {orderType === "delivery" && (
          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Delivery Address
            </label>
            <input
              required
              value={deliveryAddress}
              onChange={(e) => setDeliveryAddress(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base focus:border-nawab-maroon-400 focus:outline-none"
            />
          </div>
        )}

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">Order Items</label>
          <div className="space-y-2">
            {items.map((item, i) => (
              <div key={i} className="flex gap-2">
                <input
                  ref={(el) => {
                    itemNameRefs.current[i] = el;
                  }}
                  placeholder="Item"
                  value={item.name}
                  onChange={(e) => updateItem(i, { name: e.target.value })}
                  onKeyDown={(e) => handleItemKeyDown(e, i)}
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-nawab-maroon-400 focus:outline-none"
                />
                <input
                  type="number"
                  min={1}
                  value={item.quantity}
                  onChange={(e) => updateItem(i, { quantity: Number(e.target.value) || 1 })}
                  className="w-16 rounded-lg border border-gray-300 px-2 py-2 text-center text-base focus:border-nawab-maroon-400 focus:outline-none"
                />
                <input
                  placeholder="Notes"
                  value={item.notes ?? ""}
                  onChange={(e) => updateItem(i, { notes: e.target.value })}
                  className="w-32 rounded-lg border border-gray-300 px-2 py-2 text-base focus:border-nawab-maroon-400 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => removeItemRow(i)}
                  className="rounded-lg px-2 text-gray-400 hover:text-red-500"
                  aria-label="Remove item"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => addItemRow()}
            className="mt-2 text-sm font-medium text-nawab-maroon-600 hover:underline"
          >
            + Add item (or press Enter)
          </button>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Total Amount</label>
            <input
              required
              type="number"
              step="0.01"
              min={0}
              value={totalAmount}
              onChange={(e) => setTotalAmount(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base focus:border-nawab-maroon-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Payment Method
            </label>
            <div className="flex gap-2">
              {(["cash", "other"] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setPaymentMethod(m)}
                  className={`flex-1 rounded-lg border py-2.5 text-sm font-semibold capitalize transition ${
                    paymentMethod === m
                      ? "border-nawab-maroon-600 bg-nawab-maroon-50 text-nawab-maroon-700"
                      : "border-gray-300 text-gray-500"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Order Notes (optional)
          </label>
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. extra spicy, leave at door"
            className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base focus:border-nawab-maroon-400 focus:outline-none"
          />
        </div>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-300 py-3 font-semibold text-gray-600 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="flex-1 rounded-lg bg-nawab-maroon-600 py-3 font-semibold text-white hover:bg-nawab-maroon-700 disabled:opacity-60"
          >
            {submitting ? "Saving…" : editingOrder ? "Save Changes" : "Create Order"}
          </button>
        </div>
      </form>
    </div>
  );
}
