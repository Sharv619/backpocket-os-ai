export type OrderStatus =
  | "new"
  | "preparing"
  | "ready"
  | "out_for_delivery"
  | "delivered"
  | "cancelled";

export type OrderType = "delivery" | "pickup";

export type PaymentMethod = "cash" | "other";

export interface OrderItem {
  name: string;
  quantity: number;
  notes?: string;
}

export interface Order {
  id: string;
  customerName: string;
  customerPhone: string;
  deliveryAddress: string;
  orderItems: OrderItem[];
  totalAmount: number;
  orderType: OrderType;
  status: OrderStatus;
  assignedDriverId: string | null;
  createdAt: number | null;
  acceptedAt: number | null;
  readyAt: number | null;
  pickedUpAt: number | null;
  deliveredAt: number | null;
  cancelledAt: number | null;
  cancelReason?: string;
  notes: string;
  paymentMethod: PaymentMethod;
  createdBy: string;
  issue?: OrderIssue | null;
}

export interface OrderIssue {
  note: string;
  flaggedAt: number;
  resolved: boolean;
}

export type DriverStatus = "online" | "offline";

export interface Driver {
  id: string;
  name: string;
  phone: string;
  pinHash?: string;
  status: DriverStatus;
  currentOrderId: string | null;
  fcmToken: string | null;
}

export type StaffRole = "owner" | "staff";

export interface StaffMember {
  id: string;
  name: string;
  email: string;
  role: StaffRole;
}

export const ORDER_STATUS_FLOW: OrderStatus[] = [
  "new",
  "preparing",
  "ready",
  "out_for_delivery",
  "delivered",
];

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  new: "New",
  preparing: "Preparing",
  ready: "Ready",
  out_for_delivery: "Out for Delivery",
  delivered: "Delivered",
  cancelled: "Cancelled",
};
