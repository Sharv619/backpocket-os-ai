import type { Order, OrderStatus } from "@/types";
import { ORDER_STATUS_FLOW } from "@/types";

/** Returns the next status in the flow, or null if there is none (delivered/cancelled). */
export function nextStatus(order: Order): OrderStatus | null {
  if (order.status === "cancelled") return null;
  const idx = ORDER_STATUS_FLOW.indexOf(order.status);
  if (idx === -1 || idx === ORDER_STATUS_FLOW.length - 1) return null;
  const next = ORDER_STATUS_FLOW[idx + 1];
  // Pickup orders skip the driving leg entirely.
  if (order.orderType === "pickup" && next === "out_for_delivery") {
    return "delivered";
  }
  return next;
}

export function nextStatusLabel(order: Order): string {
  const next = nextStatus(order);
  if (!next) return "";
  switch (next) {
    case "preparing":
      return "Start Preparing";
    case "ready":
      return "Mark Ready";
    case "out_for_delivery":
      return "Send Out for Delivery";
    case "delivered":
      return order.orderType === "pickup" ? "Mark Picked Up" : "Mark Delivered";
    default:
      return "";
  }
}

/** Timestamp (ms) marking how long an order has been sitting in its current status. */
export function statusEnteredAt(order: Order): number {
  switch (order.status) {
    case "new":
      return order.createdAt ?? Date.now();
    case "preparing":
      return order.acceptedAt ?? order.createdAt ?? Date.now();
    case "ready":
      return order.readyAt ?? order.createdAt ?? Date.now();
    case "out_for_delivery":
      return order.pickedUpAt ?? order.createdAt ?? Date.now();
    default:
      return order.createdAt ?? Date.now();
  }
}

export type UrgencyLevel = "normal" | "warning" | "critical";

/** Color-codes a card by how long it has sat in its current (non-terminal) status. */
export function urgencyLevel(order: Order, now = Date.now()): UrgencyLevel {
  if (order.status === "delivered" || order.status === "cancelled") return "normal";
  const minutes = (now - statusEnteredAt(order)) / 60_000;
  if (minutes >= 20) return "critical";
  if (minutes >= 10) return "warning";
  return "normal";
}

export const URGENCY_CARD_CLASSES: Record<UrgencyLevel, string> = {
  normal: "border-l-4 border-nawab-maroon-100 bg-white",
  warning: "border-l-4 border-orange-400 bg-orange-50",
  critical: "border-l-4 border-red-500 bg-red-50",
};

export function minutesSince(ms: number | null, now = Date.now()): number {
  if (!ms) return 0;
  return Math.max(0, Math.round((now - ms) / 60_000));
}

export function timeSinceLabel(ms: number | null, now = Date.now()): string {
  const mins = minutesSince(ms, now);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  const remMins = mins % 60;
  return `${hours}h ${remMins}m ago`;
}
