import { useEffect, useRef, useState } from "react";
import type { Order } from "@/types";
import { playNewOrderChime } from "@/lib/notificationSound";

export interface DashboardToast {
  id: string;
  kind: "new_order" | "issue";
  message: string;
}

export function useDashboardAlerts(orders: Order[]) {
  const [toasts, setToasts] = useState<DashboardToast[]>([]);
  const seenOrderIds = useRef<Set<string> | null>(null);
  const seenIssueIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (typeof Notification !== "undefined" && Notification.permission === "default") {
      void Notification.requestPermission();
    }
  }, []);

  useEffect(() => {
    // First load: remember what's already there, don't alert retroactively.
    if (seenOrderIds.current === null) {
      seenOrderIds.current = new Set(orders.map((o) => o.id));
      seenIssueIds.current = new Set(
        orders.filter((o) => o.issue && !o.issue.resolved).map((o) => o.id),
      );
      return;
    }

    const newToasts: DashboardToast[] = [];

    for (const order of orders) {
      if (!seenOrderIds.current.has(order.id)) {
        seenOrderIds.current.add(order.id);
        newToasts.push({
          id: `${order.id}-new`,
          kind: "new_order",
          message: `New order from ${order.customerName} — ${order.orderType === "pickup" ? "pickup" : "delivery"}`,
        });
      }

      const hasOpenIssue = Boolean(order.issue && !order.issue.resolved);
      if (hasOpenIssue && !seenIssueIds.current.has(order.id)) {
        seenIssueIds.current.add(order.id);
        newToasts.push({
          id: `${order.id}-issue-${order.issue?.flaggedAt}`,
          kind: "issue",
          message: `Driver flagged an issue on ${order.customerName}'s order: ${order.issue?.note}`,
        });
      } else if (!hasOpenIssue) {
        seenIssueIds.current.delete(order.id);
      }
    }

    if (newToasts.length > 0) {
      setToasts((prev) => [...prev, ...newToasts]);
      playNewOrderChime();
      if (typeof Notification !== "undefined" && Notification.permission === "granted" && document.hidden) {
        for (const t of newToasts) new Notification("Nawab's Minto", { body: t.message });
      }
    }
  }, [orders]);

  function dismiss(id: string) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  return { toasts, dismiss };
}
