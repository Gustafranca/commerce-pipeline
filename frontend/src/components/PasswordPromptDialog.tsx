import { useState } from "react";
import { Modal } from "./Modal";
import { formatApiErrorBody } from "../lib/errors";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  confirmLabel?: string;
  onConfirm: (password: string) => void | Promise<void>;
};

export function PasswordPromptDialog({
  open,
  onOpenChange,
  title,
  confirmLabel = "Confirm",
  onConfirm,
}: Props) {
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!password.trim()) return;
    setBusy(true);
    setError("");
    try {
      await onConfirm(password);
      setPassword("");
      onOpenChange(false);
    } catch (err: unknown) {
      const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
      setError(formatApiErrorBody(body) || (err instanceof Error ? err.message : "Request failed."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={open}
      onOpenChange={(o) => {
        if (!o) {
          setPassword("");
          setError("");
        }
        onOpenChange(o);
      }}
      title={title}
      description="Re-enter your dashboard password to authorize this action."
    >
      <input
        type="password"
        autoComplete="current-password"
        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") void submit();
        }}
      />
      {error ? <p className="mt-2 text-xs text-red-700 whitespace-pre-wrap">{error}</p> : null}
      <div className="mt-4 flex justify-end gap-2">
        <button
          type="button"
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          onClick={() => onOpenChange(false)}
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={busy || !password.trim()}
          className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          onClick={() => void submit()}
        >
          {busy ? "…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
