import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useDriverAuth } from "@/hooks/useDriverAuth";

export function DriverLogin() {
  const { signIn } = useDriverAuth();
  const navigate = useNavigate();
  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(phone, pin);
      navigate("/driver/home", { replace: true });
    } catch {
      setError("Couldn't sign in — check the phone number and PIN.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-nawab-maroon-900 px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-xl"
      >
        <h1 className="mb-1 text-center font-display text-2xl font-bold text-nawab-maroon-600">
          Nawab&apos;s Minto
        </h1>
        <p className="mb-6 text-center text-sm text-gray-500">Driver App</p>

        <label className="mb-1 block text-sm font-medium text-gray-700">Phone Number</label>
        <input
          type="tel"
          required
          autoFocus
          inputMode="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="mb-4 w-full rounded-lg border border-gray-300 px-4 py-4 text-lg focus:border-nawab-maroon-400 focus:outline-none"
          placeholder="04XX XXX XXX"
        />

        <label className="mb-1 block text-sm font-medium text-gray-700">PIN</label>
        <input
          type="password"
          required
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
          className="mb-4 w-full rounded-lg border border-gray-300 px-4 py-4 text-center text-2xl tracking-[0.5em] focus:border-nawab-maroon-400 focus:outline-none"
        />

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-nawab-maroon-600 py-4 text-lg font-bold text-white transition hover:bg-nawab-maroon-700 disabled:opacity-60"
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
