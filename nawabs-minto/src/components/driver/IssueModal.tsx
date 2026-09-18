import { useState } from "react";
import type { Order } from "@/types";
import { flagIssue } from "@/hooks/useOrders";

const QUICK_REASONS = ["Customer not answering", "Wrong address", "Can't find entrance"];

export function IssueModal({ order, onClose }: { order: Order; onClose: () => void }) {
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (!note.trim()) return;
    setSubmitting(true);
    try {
      await flagIssue(order.id, note.trim());
      onClose();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center">
      <div className="w-full max-w-sm rounded-t-2xl bg-white p-6 shadow-2xl sm:rounded-2xl">
        <h2 className="mb-4 text-lg font-bold text-red-600">Flag an Issue</h2>

        <div className="mb-4 flex flex-wrap gap-2">
          {QUICK_REASONS.map((r) => (
            <button
              key={r}
              onClick={() => setNote(r)}
              className={`rounded-full border px-3 py-2 text-sm ${
                note === r ? "border-red-500 bg-red-50 text-red-700" : "border-gray-300 text-gray-600"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        <textarea
          autoFocus
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Describe the issue…"
          rows={3}
          className="mb-4 w-full rounded-lg border border-gray-300 p-3 text-base focus:border-red-400 focus:outline-none"
        />

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-300 py-3 font-semibold text-gray-600"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!note.trim() || submitting}
            className="flex-1 rounded-lg bg-red-600 py-3 font-semibold text-white disabled:opacity-50"
          >
            {submitting ? "Sending…" : "Send Alert"}
          </button>
        </div>
      </div>
    </div>
  );
}
