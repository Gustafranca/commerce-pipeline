import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { DashboardLoginCard } from "../components/DashboardLoginCard";
import { Modal } from "../components/Modal";
import { PageLayout } from "../components/PageLayout";
import { PasswordPromptDialog } from "../components/PasswordPromptDialog";
import { STAGED_ENTITY_OPTIONS } from "../data/tables";
import {
  deleteStagedRecord,
  fetchStagedRecords,
  patchStagedRecord,
  promoteStagedRecord,
} from "../lib/api";
import { formatApiErrorBody } from "../lib/errors";

type StagedRow = {
  id: number;
  entity_name: string;
  run_id: string;
  staged_at: string | null;
  payload: unknown;
};

function isStagedRow(x: unknown): x is StagedRow {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return typeof o.id === "number" && typeof o.entity_name === "string";
}

export function StagedPage() {
  const { authorization, isLoggedIn, oneOffAuth } = useAuth();
  const [rows, setRows] = useState<StagedRow[]>([]);
  const [entityFilter, setEntityFilter] = useState<string>("");
  const [selected, setSelected] = useState<Set<number>>(() => new Set());
  const [loadError, setLoadError] = useState("");
  const [busy, setBusy] = useState(false);

  const [editOpen, setEditOpen] = useState(false);
  const [editRow, setEditRow] = useState<StagedRow | null>(null);
  const [editEntity, setEditEntity] = useState("");
  const [editJson, setEditJson] = useState("");
  const [editError, setEditError] = useState("");

  const [pwdOpen, setPwdOpen] = useState(false);
  const [pwdMode, setPwdMode] = useState<"delete" | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);

  const [actionMsg, setActionMsg] = useState("");

  const load = useCallback(async () => {
    if (!authorization) {
      setRows([]);
      setLoadError("");
      return;
    }
    setLoadError("");
    setBusy(true);
    try {
      const data = await fetchStagedRecords(authorization, { limit: 500 });
      const list = Array.isArray(data) ? data : [];
      setRows(list.filter(isStagedRow));
      setSelected(new Set());
    } catch (err: unknown) {
      const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
      setLoadError(formatApiErrorBody(body));
      setRows([]);
    } finally {
      setBusy(false);
    }
  }, [authorization]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    if (!entityFilter) return rows;
    return rows.filter((r) => r.entity_name === entityFilter);
  }, [rows, entityFilter]);

  function openEdit(row: StagedRow) {
    setEditRow(row);
    setEditEntity(row.entity_name);
    setEditJson(JSON.stringify(row.payload ?? {}, null, 2));
    setEditError("");
    setEditOpen(true);
  }

  async function saveEdit() {
    if (!authorization || !editRow) return;
    let payload: unknown;
    try {
      payload = JSON.parse(editJson) as unknown;
    } catch {
      setEditError("Invalid JSON in payload.");
      return;
    }
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      setEditError("Payload must be a JSON object.");
      return;
    }
    setEditError("");
    try {
      await patchStagedRecord(authorization, editRow.id, {
        payload,
        ...(editEntity !== editRow.entity_name ? { entity_name: editEntity } : {}),
      });
      setEditOpen(false);
      setActionMsg("Record updated.");
      await load();
    } catch (err: unknown) {
      const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
      setEditError(formatApiErrorBody(body));
    }
  }

  function requestDelete(id: number) {
    setDeleteTargetId(id);
    setPwdMode("delete");
    setPwdOpen(true);
  }

  async function promoteSelected() {
    if (!authorization || selected.size === 0) return;
    setActionMsg("");
    const ids = [...selected];
    const results: string[] = [];
    for (const id of ids) {
      try {
        await promoteStagedRecord(authorization, id);
        results.push(`#${id}: promoted`);
      } catch (err: unknown) {
        const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
        results.push(`#${id}: ${formatApiErrorBody(body)}`);
      }
    }
    setActionMsg(results.join("\n"));
    await load();
  }

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  if (!isLoggedIn || !authorization) {
    return (
      <PageLayout title="Staged records" subtitle="Review, edit, promote, or delete rows in staging.common_records.">
        <DashboardLoginCard title="Sign in to staged records" />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title="Staged records"
      subtitle="Review, edit, promote, or delete rows in staging.common_records."
      actions={
        <button
          type="button"
          disabled={busy}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          onClick={() => void load()}
        >
          Refresh
        </button>
      }
    >
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">Entity filter</label>
          <select
            className="mt-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
          >
            <option value="">All entities</option>
            {STAGED_ENTITY_OPTIONS.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          disabled={selected.size === 0}
          className="rounded-lg bg-emerald-700 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
          onClick={() => void promoteSelected()}
        >
          Promote selected ({selected.size})
        </button>
      </div>

      {loadError ? (
        <pre className="mb-4 whitespace-pre-wrap rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">
          {loadError}
        </pre>
      ) : null}
      {actionMsg ? (
        <pre className="mb-4 whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-100 p-3 text-xs text-slate-800">
          {actionMsg}
        </pre>
      ) : null}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-600">
            <tr>
              <th className="px-3 py-2 w-10" />
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Entity</th>
              <th className="px-3 py-2">Run</th>
              <th className="px-3 py-2">Staged</th>
              <th className="px-3 py-2">Payload</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50/80">
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={selected.has(r.id)}
                    onChange={() => toggleSelect(r.id)}
                    aria-label={`Select ${r.id}`}
                  />
                </td>
                <td className="px-3 py-2 font-mono text-xs">{r.id}</td>
                <td className="px-3 py-2">{r.entity_name}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-600">{r.run_id}</td>
                <td className="px-3 py-2 text-xs text-slate-600">{r.staged_at ?? "—"}</td>
                <td className="max-w-md truncate px-3 py-2 font-mono text-xs text-slate-700">
                  {JSON.stringify(r.payload)}
                </td>
                <td className="px-3 py-2 whitespace-nowrap">
                  <button
                    type="button"
                    className="mr-2 text-emerald-700 hover:underline"
                    onClick={() => openEdit(r)}
                  >
                    Edit
                  </button>
                  <button type="button" className="text-red-700 hover:underline" onClick={() => requestDelete(r.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && !busy ? (
          <p className="p-6 text-center text-sm text-slate-500">No staged rows match this filter.</p>
        ) : null}
      </div>

      <Modal open={editOpen} onOpenChange={setEditOpen} title="Edit staged record" description={`Record id ${editRow?.id ?? ""}`}>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500">entity_name</label>
            <select
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              value={editEntity}
              onChange={(e) => setEditEntity(e.target.value)}
            >
              {STAGED_ENTITY_OPTIONS.map((e) => (
                <option key={e} value={e}>
                  {e}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">payload (JSON object)</label>
            <textarea
              className="mt-1 h-56 w-full rounded-lg border border-slate-200 p-3 font-mono text-xs outline-none ring-slate-400 focus:ring-2"
              value={editJson}
              onChange={(e) => setEditJson(e.target.value)}
            />
          </div>
          {editError ? <pre className="text-xs text-red-700 whitespace-pre-wrap">{editError}</pre> : null}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm"
              onClick={() => setEditOpen(false)}
            >
              Cancel
            </button>
            <button
              type="button"
              className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm text-white"
              onClick={() => void saveEdit()}
            >
              Save
            </button>
          </div>
        </div>
      </Modal>

      <PasswordPromptDialog
        open={pwdOpen && pwdMode === "delete"}
        onOpenChange={(o) => {
          setPwdOpen(o);
          if (!o) {
            setPwdMode(null);
            setDeleteTargetId(null);
          }
        }}
        title="Confirm delete"
        confirmLabel="Delete"
        onConfirm={async (password) => {
          if (deleteTargetId == null) return;
          const auth = oneOffAuth(password);
          await deleteStagedRecord(auth, deleteTargetId);
          setActionMsg(`Deleted staged record #${deleteTargetId}.`);
          await load();
        }}
      />
    </PageLayout>
  );
}
