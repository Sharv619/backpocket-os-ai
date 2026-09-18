import { useEffect, useState } from "react";
import {
  addDoc,
  collection,
  doc,
  onSnapshot,
  orderBy,
  query,
  serverTimestamp,
  updateDoc,
  Timestamp,
  where,
  type QueryConstraint,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import type { Order, OrderStatus } from "@/types";

function fromFirestore(id: string, data: Record<string, unknown>): Order {
  const ts = (v: unknown) => (v instanceof Timestamp ? v.toMillis() : null);
  return {
    id,
    customerName: data.customerName as string,
    customerPhone: data.customerPhone as string,
    deliveryAddress: (data.deliveryAddress as string) ?? "",
    orderItems: (data.orderItems as Order["orderItems"]) ?? [],
    totalAmount: (data.totalAmount as number) ?? 0,
    orderType: data.orderType as Order["orderType"],
    status: data.status as OrderStatus,
    assignedDriverId: (data.assignedDriverId as string | null) ?? null,
    createdAt: ts(data.createdAt),
    acceptedAt: ts(data.acceptedAt),
    readyAt: ts(data.readyAt),
    pickedUpAt: ts(data.pickedUpAt),
    deliveredAt: ts(data.deliveredAt),
    cancelledAt: ts(data.cancelledAt),
    cancelReason: data.cancelReason as string | undefined,
    notes: (data.notes as string) ?? "",
    paymentMethod: (data.paymentMethod as Order["paymentMethod"]) ?? "cash",
    createdBy: (data.createdBy as string) ?? "",
    issue: (data.issue as Order["issue"]) ?? null,
  };
}

/** Live orders feed. Pass `activeOnly` to exclude delivered/cancelled (the Kanban view). */
export function useOrders(options?: { activeOnly?: boolean; driverId?: string }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const constraints: QueryConstraint[] = [orderBy("createdAt", "desc")];
    if (options?.driverId) {
      constraints.unshift(where("assignedDriverId", "==", options.driverId));
    }
    const q = query(collection(db, "orders"), ...constraints);
    const unsub = onSnapshot(q, (snap) => {
      let list = snap.docs.map((d) => fromFirestore(d.id, d.data()));
      if (options?.activeOnly) {
        list = list.filter((o) => o.status !== "delivered" && o.status !== "cancelled");
      }
      setOrders(list);
      setLoading(false);
    });
    return unsub;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options?.activeOnly, options?.driverId]);

  return { orders, loading };
}

export interface NewOrderInput {
  customerName: string;
  customerPhone: string;
  deliveryAddress: string;
  orderItems: Order["orderItems"];
  totalAmount: number;
  orderType: Order["orderType"];
  paymentMethod: Order["paymentMethod"];
  notes: string;
  createdBy: string;
}

export async function createOrder(input: NewOrderInput) {
  await addDoc(collection(db, "orders"), {
    ...input,
    status: "new" satisfies OrderStatus,
    assignedDriverId: null,
    createdAt: serverTimestamp(),
    acceptedAt: null,
    readyAt: null,
    pickedUpAt: null,
    deliveredAt: null,
    cancelledAt: null,
    issue: null,
  });
}

export async function updateOrderStatus(orderId: string, status: OrderStatus) {
  const timestampField: Partial<Record<OrderStatus, string>> = {
    preparing: "acceptedAt",
    ready: "readyAt",
    out_for_delivery: "pickedUpAt",
    delivered: "deliveredAt",
  };
  const field = timestampField[status];
  await updateDoc(doc(db, "orders", orderId), {
    status,
    ...(field ? { [field]: serverTimestamp() } : {}),
  });
}

export async function assignDriver(orderId: string, driverId: string) {
  await updateDoc(doc(db, "orders", orderId), { assignedDriverId: driverId });
}

export async function cancelOrder(orderId: string, reason: string) {
  await updateDoc(doc(db, "orders", orderId), {
    status: "cancelled" satisfies OrderStatus,
    cancelReason: reason,
    cancelledAt: serverTimestamp(),
  });
}

export async function editOrder(orderId: string, patch: Partial<NewOrderInput>) {
  await updateDoc(doc(db, "orders", orderId), patch);
}

export async function flagIssue(orderId: string, note: string) {
  await updateDoc(doc(db, "orders", orderId), {
    issue: { note, flaggedAt: Date.now(), resolved: false },
  });
}

export async function resolveIssue(orderId: string) {
  await updateDoc(doc(db, "orders", orderId), { issue: null });
}
