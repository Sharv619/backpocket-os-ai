import type { Order } from "@/types";
import { csvEscape } from "@/lib/format";

export function ordersToCsv(orders: Order[]): string {
  const headers = [
    "Order ID",
    "Customer",
    "Phone",
    "Type",
    "Status",
    "Total",
    "Payment",
    "Driver ID",
    "Created At",
    "Delivered At",
  ];
  const rows = orders.map((o) =>
    [
      o.id,
      o.customerName,
      o.customerPhone,
      o.orderType,
      o.status,
      o.totalAmount.toFixed(2),
      o.paymentMethod,
      o.assignedDriverId ?? "",
      o.createdAt ? new Date(o.createdAt).toISOString() : "",
      o.deliveredAt ? new Date(o.deliveredAt).toISOString() : "",
    ]
      .map(csvEscape)
      .join(","),
  );
  return [headers.join(","), ...rows].join("\n");
}

export function downloadCsv(filename: string, csv: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
