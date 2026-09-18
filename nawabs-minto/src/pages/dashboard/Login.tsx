import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useStaffAuth } from "@/hooks/useStaffAuth";

export function DashboardLogin() {
  const { signIn } = useStaffAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(email, password);
      navigate("/dashboard/board", { replace: true });
    } catch {
      setError("Couldn't sign in — check the email and password.");
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
        <p className="mb-6 text-center text-sm text-gray-500">Shop Dashboard</p>

        <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
        <input
          type="email"
          required
          autoFocus
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-4 w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-nawab-maroon-400 focus:outline-none"
          placeholder="staff@nawabsminto.com.au"
        />

        <label className="mb-1 block text-sm font-medium text-gray-700">Password</label>
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4 w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-nawab-maroon-400 focus:outline-none"
        />

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-nawab-maroon-600 py-3 font-semibold text-white transition hover:bg-nawab-maroon-700 disabled:opacity-60"
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>

        <p className="mt-6 text-center text-xs text-gray-400">
          Driver? Use the{" "}
          <a href="/driver" className="text-nawab-maroon-500 underline">
            driver app
          </a>
          .
        </p>
      </form>
    </div>
  );
}
