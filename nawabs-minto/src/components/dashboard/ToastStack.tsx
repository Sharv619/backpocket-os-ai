import type { DashboardToast } from "@/hooks/useDashboardAlerts";

export function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: DashboardToast[];
  onDismiss: (id: string) => void;
}) {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed right-4 top-4 z-[60] flex w-80 flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`animate-toast-in rounded-xl p-4 shadow-lg ${
            t.kind === "issue" ? "bg-red-600 text-white" : "bg-nawab-maroon-600 text-white"
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm font-medium">
              {t.kind === "issue" ? "⚠ " : "🔔 "}
              {t.message}
            </p>
            <button
              onClick={() => onDismiss(t.id)}
              className="shrink-0 text-white/80 hover:text-white"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
