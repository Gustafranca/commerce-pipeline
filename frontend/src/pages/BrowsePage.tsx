import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { DashboardLoginCard } from "../components/DashboardLoginCard";
import { PageLayout } from "../components/PageLayout";
import { PasswordPromptDialog } from "../components/PasswordPromptDialog";
import { BROWSE_ENTITIES, BROWSE_PK } from "../data/tables";
import { browseTable, deleteBrowseRow } from "../lib/api";
import { formatApiErrorBody } from "../lib/errors";

type BrowseResponse = {
  entity?: string;
  rows?: Record<string, unknown>[];
  limit?: number;
  offset?: number;
  count?: number;
};

export function BrowsePage() {
  const { authorization, isLoggedIn, oneOffAuth } = useAuth();
  const [entity, setEntity] = useState(BROWSE_ENTITIES[0] ?? "pedidos");
  const [offset, setOffset] = useState(0);
  const limit = 100;
  const [data, setData] = useState<BrowseResponse | null>(null);
  const [loadError, setLoadError] = useState("");
  const [busy, setBusy] = useState(false);
  const [selectedPk, setSelectedPk] = useState<number | null>(null);
  const [msg, setMsg] = useState("");
  const [pwdOpen, setPwdOpen] = useState(false);

  const pkCol = BROWSE_PK[entity] ?? "id";

  const load = useCallback(async () => {
    if (!authorization) {
      setData(null);
      setLoadError("");
      setSelectedPk(null);
      return;
    }
    setLoadError("");
    setBusy(true);
    try {
      const res = (await browseTable(authorization, entity, { limit, offset })) as BrowseResponse;
      setData(res);
      setSelectedPk(null);
    } catch (err: unknown) {
      const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
      setLoadError(formatApiErrorBody(body));
      setData(null);
    } finally {
      setBusy(false);
    }
  }, [authorization, entity, offset]);

  useEffect(() => {
    void load();
  }, [load]);

  const rows = data?.rows ?? [];
  const columns = useMemo(() => {
    if (rows.length === 0) return [] as string[];
    return Object.keys(rows[0] ?? {}).sort();
  }, [rows]);

  function cellValue(v: unknown): string {
    if (v === null || v === undefined) return "";
    if (typeof v === "object") return JSON.stringify(v);
    return String(v);
  }

  function rowPk(row: Record<string, unknown>): number | null {
    const raw = row[pkCol];
    if (typeof raw === "number" && Number.isFinite(raw)) return raw;
    if (typeof raw === "string" && raw.trim() !== "" && !Number.isNaN(Number(raw))) return Number(raw);
    return null;
  }

  if (!isLoggedIn || !authorization) {
    return (
      <PageLayout title="Browse warehouse" subtitle="Read-only listing with optional row delete (password required).">
        <DashboardLoginCard title="Sign in to browse" />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title="Browse warehouse"
      subtitle="Paged table views backed by GET /api/browse/{entity}."
      actions={
        <>
          <button
            type="button"
            disabled={busy}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            onClick={() => void load()}
          >
            Refresh
          </button>
          <button
            type="button"
            disabled={selectedPk == null}
            className="rounded-lg bg-red-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-800 disabled:opacity-50"
            onClick={() => setPwdOpen(true)}
          >
            Delete selected row
          </button>
        </>
      }
    >
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">Table</label>
          <select
            className="mt-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
            value={entity}
            onChange={(e) => {
              setEntity(e.target.value);
              setOffset(0);
            }}
          >
            {BROWSE_ENTITIES.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
        </div>
        <div className="text-xs text-slate-500">
          Primary key: <span className="font-mono">{pkCol}</span> · limit {limit} · offset {offset}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={offset === 0 || busy}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm disabled:opacity-50"
            onClick={() => setOffset((o) => Math.max(0, o - limit))}
          >
            Previous page
          </button>
          <button
            type="button"
            disabled={busy || rows.length < limit}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm disabled:opacity-50"
            onClick={() => setOffset((o) => o + limit)}
          >
            Next page
          </button>
        </div>
      </div>

      {loadError ? (
        <pre className="mb-4 whitespace-pre-wrap rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">
          {loadError}
        </pre>
      ) : null}
      {msg ? (
        <pre className="mb-4 whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-100 p-3 text-xs">{msg}</pre>
      ) : null}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-600">
            <tr>
              <th className="px-2 py-2 w-10" />
              {columns.map((c) => (
                <th key={c} className="px-3 py-2 whitespace-nowrap">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row, idx) => {
              const id = rowPk(row);
              const sel = id != null && selectedPk === id;
              return (
                <tr
                  key={`${id ?? idx}`}
                  className={sel ? "bg-emerald-50" : "cursor-pointer hover:bg-slate-50/80"}
                  onClick={() => {
                    if (id != null) setSelectedPk(id);
                  }}
                >
                  <td className="px-2 py-2 text-center">
                    <input
                      type="radio"
                      name="browse-pk"
                      checked={sel}
                      onChange={() => id != null && setSelectedPk(id)}
                      aria-label={`Select row ${id}`}
                    />
                  </td>
                  {columns.map((c) => (
                    <td key={c} className="max-w-xs truncate px-3 py-2 font-mono text-xs text-slate-800">
                      {cellValue(row[c])}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
        {rows.length === 0 && !busy ? (
          <p className="p-6 text-center text-sm text-slate-500">No rows in this page.</p>
        ) : null}
      </div>

      <PasswordPromptDialog
        open={pwdOpen}
        onOpenChange={setPwdOpen}
        title="Delete warehouse row"
        confirmLabel="Delete"
        onConfirm={async (password) => {
          if (selectedPk == null) return;
          const auth = oneOffAuth(password);
          await deleteBrowseRow(auth, entity, selectedPk);
          setMsg(`Deleted ${entity} ${pkCol}=${selectedPk}.`);
          setPwdOpen(false);
          await load();
        }}
      />
    </PageLayout>
  );
}
