import { useMemo, useState } from "react";
import { useOrders } from "@/hooks/useOrders";
import { useDrivers } from "@/hooks/useDrivers";
import { formatCurrency } from "@/lib/format";
import { ordersToCsv, downloadCsv } from "@/lib/csv";
import { ORDER_STATUS_LABELS } from "@/types";
import type { OrderStatus } from "@/types";

export function DashboardHistory() {
  const { orders } = useOrders();
  const { drivers } = useDrivers();

  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "all">("all");
  const [driverFilter, setDriverFilter] = useState<string>("all");

  const filtered = useMemo(() => {
    return orders.filter((o) => {
      if (!o.createdAt) return false;
      if (fromDate && o.createdAt < new Date(fromDate).getTime()) return false;
      if (toDate && o.createdAt > new Date(toDate).getTime() + 86_400_000) return false;
      if (statusFilter !== "all" && o.status !== statusFilter) return false;
      if (driverFilter !== "all" && o.assignedDriverId !== driverFilter) return false;
      return true;
    });
  }, [orders, fromDate, toDate, statusFilter, driverFilter]);

  const summary = useMemo(() => {
    const delivered = filtered.filter((o) => o.status === "delivered");
    const totalRevenue = filtered
      .filter((o) => o.status !== "cancelled")
      .reduce((sum, o) => sum + o.totalAmount, 0);
    const avgDeliveryMinutes =
      delivered.length > 0
        ? delivered.reduce((sum, o) => {
            if (!o.createdAt || !o.deliveredAt) return sum;
            return sum + (o.deliveredAt - o.createdAt) / 60_000;
          }, 0) / delivered.length
        : 0;
    return {
      totalOrders: filtered.length,
      totalRevenue,
      avgDeliveryMinutes: Math.round(avgDeliveryMinutes),
    };
  }, [filtered]);

  return (
    <div className="p-4 sm:p-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-2xl font-bold text-nawab-maroon-700">
          Order History
        </h1>
        <button
          onClick={() => downloadCsv(`orders-${Date.now()}.csv`, ordersToCsv(filtered))}
          className="rounded-lg border border-nawab-maroon-300 px-4 py-2 text-sm font-semibold text-nawab-maroon-600 hover:bg-nawab-maroon-50"
        >
          Export CSV
        </button>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 rounded-xl bg-white p-4 shadow-sm sm:grid-cols-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">From</label>
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-2 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">To</label>
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-2 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">Status</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as OrderStatus | "all")}
            className="w-full rounded-lg border border-gray-300 px-2 py-2 text-sm"
          >
            <option value="all">All</option>
            {Object.entries(ORDER_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">Driver</label>
          <select
            value={driverFilter}
            onChange={(e) => setDriverFilter(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-2 py-2 text-sm"
          >
            <option value="all">All</option>
            {drivers.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500">Total Orders</p>
          <p className="text-2xl font-bold text-nawab-maroon-700">{summary.totalOrders}</p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500">Total Revenue</p>
          <p className="text-2xl font-bold text-nawab-maroon-700">
            {formatCurrency(summary.totalRevenue)}
          </p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-gray-500">Avg. Delivery Time</p>
          <p className="text-2xl font-bold text-nawab-maroon-700">
            {summary.avgDeliveryMinutes} min
          </p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-xs uppercase text-gray-400">
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Driver</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((o) => (
              <tr key={o.id} className="border-b border-gray-50">
                <td className="px-4 py-3 font-medium text-gray-800">{o.customerName}</td>
                <td className="px-4 py-3 capitalize text-gray-500">{o.orderType}</td>
                <td className="px-4 py-3 text-gray-500">{ORDER_STATUS_LABELS[o.status]}</td>
                <td className="px-4 py-3 text-gray-800">{formatCurrency(o.totalAmount)}</td>
                <td className="px-4 py-3 text-gray-500">
                  {drivers.find((d) => d.id === o.assignedDriverId)?.name ?? "—"}
                </td>
                <td className="px-4 py-3 text-gray-400">
                  {o.createdAt ? new Date(o.createdAt).toLocaleString("en-AU") : "—"}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  No orders match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
