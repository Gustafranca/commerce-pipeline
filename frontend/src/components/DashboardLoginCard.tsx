import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { fetchStagedRecords } from "../lib/api";
import { basicAuthHeader } from "../lib/basicAuth";
import { formatApiErrorBody } from "../lib/errors";

export function DashboardLoginCard({ title = "Dashboard sign-in" }: { title?: string }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const auth = basicAuthHeader(username.trim(), password);
    setBusy(true);
    try {
      await fetchStagedRecords(auth, { limit: 1 });
      login(username.trim(), password);
      setPassword("");
    } catch (err: unknown) {
      const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
      setError(formatApiErrorBody(body) || "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <p className="mt-1 text-sm text-slate-600">Use the same Basic credentials as the legacy dashboard.</p>
      <form className="mt-4 space-y-3" onSubmit={(e) => void handleSubmit(e)}>
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">Username</label>
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">Password</label>
          <input
            type="password"
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error ? (
          <pre className="whitespace-pre-wrap rounded-lg bg-red-50 p-3 text-xs text-red-800">{error}</pre>
        ) : null}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-slate-900 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
